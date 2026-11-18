"""APIを呼ばず、並列のPython起動とファイル読込の下で実際のフックを測る。"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import venv
import bench_prompt_hook as bench

LOAD = """import sys, pathlib, subprocess, os, json, time
root, stop, report = map(pathlib.Path, sys.argv[1:4])
code = 'import dataclasses,json,ctypes,ssl,urllib.request;from pathlib import Path;p=Path(' + repr(str(root)) + ');data=[f.read_bytes() for f in p.rglob(\"*.md\")];print(json.dumps({\"files\":len(data),\"bytes\":sum(map(len,data))}))'
flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
count, total_bytes, start = 0, 0, time.perf_counter()
while not stop.exists():
    proc = subprocess.run([sys.executable, '-I', '-S', '-c', code], capture_output=True, creationflags=flags, timeout=10)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode('utf-8', 'replace'))
    value = json.loads(proc.stdout)
    count += 1
    total_bytes += value['bytes']
report.write_text(json.dumps({'cycles':count,'bytes_read':total_bytes,'elapsed_ms':round((time.perf_counter()-start)*1000,1)}), encoding='utf-8')
"""


def profile_copy(path, hook_source):
    source = hook_source.read_text(encoding='utf-8')
    source = source.replace('from __future__ import annotations', 'from __future__ import annotations\nimport time as _bench_time\n_bench_started = _bench_time.perf_counter()')
    source = source.replace('sys.path.insert(0, str(Path(__file__).resolve().parent))', f'sys.path.insert(0, {str(bench.SCRIPTS)!r})')
    helper = r"""
def _bench_stamp(phase):
    with open(os.environ['BENCH_PROFILE'], 'ab') as stream:
        stream.write((json.dumps({'phase':phase, 'at':time.perf_counter(), 'entry':_bench_started, 'pid':os.getpid(), 'python':sys.executable})+'\n').encode('utf-8'))
"""
    source = source.replace('DEADLINE_SECONDS = 2.5', 'DEADLINE_SECONDS = 2.5\n' + helper)
    source = source.replace('    started = time.monotonic()', '    _bench_stamp("parent_imported")\n    started = time.monotonic()')
    source = source.replace('        import wiki_prompt_context as context', '        import wiki_prompt_context as context\n        _bench_stamp("context_imported")')
    source = source.replace('        picked = context.select(', '        _bench_stamp("before_select")\n        picked = context.select(')
    source = source.replace('        if picked is not None:', '        _bench_stamp("selected")\n        if picked is not None:')
    source = source.replace('        if result.returncode == 0', '        _bench_stamp("worker_returned")\n        if result.returncode == 0')
    compile(source, "<profile-hook>", "exec")
    path.write_text(source, encoding='utf-8', newline='\n')


def run(args):
    with tempfile.TemporaryDirectory(prefix='wiki-hook-parallel-') as tmp:
        base = Path(tmp)
        project = base / 'project'
        bench.synthetic_wiki(project / 'wiki', args.pages)
        if args.query == 'names':
            for i, title in ((0, '固有の候補資料アルファ'), (1, '固有の候補資料ベータ')):
                path = project / 'wiki' / 'concepts' / f'page-{i:04d}.md'
                content = path.read_text(encoding='utf-8')
                old = json.loads(next(line.removeprefix('title: ') for line in content.splitlines() if line.startswith('title: ')))
                path.write_text(content.replace(old, title), encoding='utf-8', newline='\n')
        active = project / '.venv'
        if args.venv != 'none':
            venv.EnvBuilder(with_pip=False).create(active)
        stop = base / 'stop'
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        jobs = [subprocess.Popen([sys.executable, '-I', '-c', LOAD, str(project), str(stop), str(base / f'load-{i}.json')],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
                for i in range(args.load_workers)]
        try:
            hook = args.hook or bench.SCRIPTS / 'wiki_prompt_hook.py'
            if args.profile:
                hook = base / 'profile_hook.py'
                profile_copy(hook, args.hook or bench.SCRIPTS / 'wiki_prompt_hook.py')
            command = bench.shell_line(hook.resolve())
            if args.registration:
                command = json.loads(args.registration.read_text(encoding='utf-8'))['hooks']['UserPromptSubmit'][0]['hooks'][0]['command']
                command = command.replace('${CLAUDE_PLUGIN_ROOT}/skills/info-hive/scripts/wiki_prompt_hook.py', hook.resolve().as_posix())
            argv = [bench.bash_path(), '-c', command]
            env = dict(os.environ, CLAUDE_PLUGIN_DATA=str(base / 'data'), INFO_HIVE_PROMPT_CONTEXT='1')
            env.pop('VIRTUAL_ENV', None)
            if args.venv == 'active':
                env['VIRTUAL_ENV'] = str(active)
            prompt = ('[[page-0000]] [[page-0001]] の手順を確認して' if args.query == 'direct'
                      else '固有の候補資料アルファと固有の候補資料ベータの手順を確認して')
            env.pop("RUST_LOG", None)  # 実行ホストのデバッグの設定は測定条件から外す。
            def once(i):
                profile = base / f'profile-{i}.jsonl'
                current_env = dict(env, BENCH_PROFILE=str(profile))
                payload = json.dumps({'prompt':prompt,
                                      'cwd':str(project),'session_id':f'parallel-{i}','hook_event_name':'UserPromptSubmit'}).encode('utf-8')
                before = time.perf_counter()
                proc = subprocess.run(argv,input=payload,capture_output=True,env=current_env,cwd=project,timeout=20)
                elapsed = time.perf_counter()-before
                rows = [json.loads(line) for line in profile.read_text(encoding='utf-8').splitlines()] if profile.exists() else []
                valid = proc.returncode == 0 and not proc.stderr and bench.valid_candidate_output(proc.stdout)
                return {'ms':round(elapsed*1000,1),'exit':proc.returncode,'delivered':valid,'stdout_bytes':len(proc.stdout),
                        'stderr':proc.stderr.decode('utf-8','replace')[:500],
                        'profile':[{**r,'since_launch_ms':round((r['at']-before)*1000,1),'import_ms':round((r['at']-r['entry'])*1000,1)} for r in rows]}
            warmup = once(-1)
            if warmup["stderr"] or warmup["exit"]:
                raise RuntimeError('ウォームアップで起動が失敗した: ' + warmup["stderr"])
            if any(job.poll() is not None for job in jobs):
                raise RuntimeError('測定前に並列負荷が終了した')
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                trials=list(pool.map(once,range(args.runs)))
            result = {'pages':args.pages,'runs':args.runs,'load_workers':args.load_workers,'concurrency':args.concurrency,'profiled':args.profile,'venv':args.venv,'query_kind':args.query,'prompt':prompt,
                    'excluded_env':['RUST_LOG'], 'load':'各workerが新しいPythonを繰り返し起動し、標準ライブラリの読込と合成wiki全ファイルの読込を行う。API・ネットワーク・他のプロセスの操作はない。',
                    'timing':bench.summary([r['ms']/1000 for r in trials]),'delivered':sum(r['delivered'] for r in trials),
                    'command':command, 'source_sha256':hashlib.sha256((args.hook or bench.SCRIPTS / 'wiki_prompt_hook.py').read_bytes()).hexdigest(),
                    'context_sha256':hashlib.sha256((bench.SCRIPTS / 'wiki_prompt_context.py').read_bytes()).hexdigest(),
                    'pages_sha256':hashlib.sha256((bench.SCRIPTS / 'wiki_pages.py').read_bytes()).hexdigest(),
                    'warmup':warmup, 'trials':trials}
        finally:
            stop.touch()
            for job in jobs:
                try:
                    job.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    job.terminate()
                    job.wait(timeout=5)
        load_reports = [json.loads((base / f'load-{i}.json').read_text(encoding='utf-8')) for i in range(args.load_workers)]
        if any(job.returncode or value['cycles'] < 1 for job,value in zip(jobs,load_reports)):
            raise RuntimeError('並列負荷の実行を確認できない')
        result['load_actual'] = load_reports
        return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pages',type=int,default=150)
    parser.add_argument('--runs',type=int,default=20)
    parser.add_argument('--load-workers',type=int,default=4)
    parser.add_argument('--concurrency',type=int,default=4)
    parser.add_argument('--profile',action='store_true')
    parser.add_argument('--venv',choices=('none','cwd','active'),default='none')
    parser.add_argument('--query',choices=('direct','names'),default='direct')
    parser.add_argument('--hook',type=Path)
    parser.add_argument('--registration',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    data=run(args)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in data.items() if k!='trials'},ensure_ascii=False))
