---
url: "https://levelup.gitconnected.com/building-dynamic-workflows-a-new-agentic-system-d304abd20dd0"
title: "Building Dynamic Workflows: A New Agentic System"
fetched_at: "2026-11-19T15:39:49+09:00"
source_sha256: "6d192a66059e4c853b333be4217f30e7726947789841c06112070d3f93527ab7"
source_sha256_of: "dom"
fetch_method: "playwright"
source_lang: "en"
translated_by: "Claude Sonnet 5.5"
fetched_by: "wiki_fetch.py 0.1"
browser_session: "existing"
---

# 動的ワークフローの構築: 新しいエージェントシステム

## リードモデルが検査済みの短いプログラムとして計画を書き、素の Python が並列のワーカーでそれを実行する

[Fareed Khan](https://medium.com/@fareedkhandev?source=post_page---byline--d304abd20dd0------------------------------------------)

34 分ほどで読める記事で、2026年10月19日に公開された

マルチエージェントシステムの多くは、2 通りのどちらかで動く。リードエージェントがヘルパーを 1 つずつ呼び出して報告のたびに待つか、エンジニアが、どの仕事でも同じ手順を実行するパイプラインを固定で書くかである。新しい方法である[**Anthropic が導入した動的ワークフロー（dynamic workflow）**](https://x.com/ClaudeDevs/status/2108591328732856655)は、リードが計画の全体を短いプログラムとして一度だけ書き、素のコードが多数のワーカーを並列に使ってそれを実行する。

![](https://miro.medium.com/v2/resize:fit:7137/1*gi93Z001rGI0G97oYI2TfQ.png)（未取得）

動的ワークフローシステムのアーキテクチャ（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

これから構築するアーキテクチャを、1 つずつ部品を組み立てながら示す。

- **ベンチマーク**: 72 個の埋め込みバグと、指摘を非公開の正解キーに照らして採点する採点器。
- **回答をためておく台帳**: キャッシュ、リプレイ、クラッシュからの復旧。
- **ランタイム**: 1 つの予算のもとで、並列のフェーズとして動くワーカー。
- **監査キット**: スキャンを行うワーカーと、見つかったものに投票する懐疑者（skeptic）。
- **計画の言語**: 制限付きの Python で、費用が発生する前に検査される。
- **リード**: コードの代わりに、500 トークンのファクトシート（fact sheet）を読む。
- **評価のパート**: 5 つの設計とアブレーション。

最終的に、そのシートだけを読むリードは、埋め込まれたバグの平均 0.45 を見つける。人が書いた計画では 0.30、エージェント 1 つだけでは 0.02 である。コードの全体は、私の GitHub リポジトリ dynamic-workflow-agents にある。

書いていくファイルは次のとおりである。

```
dynamic-workflows/
├── build/
│   ├── config.py     # model roles, prices, paths
│   ├── bench.py      # the hidden key and the scorer
│   ├── shards.py     # code packed into shards
│   ├── llm.py        # replies, ledger, front door, budget
│   ├── runtime.py    # threads, parallel, background runs
│   ├── kit.py        # scan, check, vote and report
│   ├── plans.py      # whitelist, dry run, approval gate
│   ├── lead.py       # fact sheet in, program out
│   └── prompts.json  # the instructions each role reads
└── data/algorithms/  # the library, the bugs and the key
```

## マルチエージェントシステムがよく失敗する理由

失敗の多くは 2 つの限界から来る。1 つのエージェントが保持できるテキストには限りがあり、大きな仕事では、読んだ内容を忘れたり、早く止まったりする。タスクを 1 つずつ配るリードはボトルネックになり、そのコンテキストは報告のたびに増える。

![](https://miro.medium.com/v2/resize:fit:6027/1*Wy0O_fhcUdjo6-Bqs0UfzA.png)（未取得）

1 つのエージェントがターンをどう使うか（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

私たちの監査は、その両方を示している。対象は Python ファイル 849 個、約 135 万トークンで、私自身が 72 個のバグを埋め込んだ。エージェント 1 つだけでは、3 回の実行でそれぞれ 0 個、1 個、4 個を見つけ、毎回自分で止まった。ヘルパーを使うリードは 14 のシャードをすべて読んだが、見つけたバグは 12 個だけだった。

## 動的ワークフローの設計

どの仕事も 6 つのステップを通る。

- **偵察する**: 素のコードが仕事を読み、1 ページのファクトシートを書く。
- **計画を立てる**: リードがそのシートから短い Python プログラムを書く。
- **検査する**: ホワイトリストが、計画に許されないことをすべて拒否する。
- **リハーサル**: 無料の代役モデルが計画を 1 回実行して費用を見積もる。
- **承認する**: ゲートが計画を通すか、人の判断のために保留する。
- **実行する**: ランタイムが 1 つの予算のもとで、計画をバックグラウンドで実行する。

![](https://miro.medium.com/v2/resize:fit:6234/1*KWiPXA3NJxuLRg2xzadQ0w.png)（未取得）

同じ仕事に対する 3 つの設計（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

比較を実行する前に、私は 11 個の予測を書き留めた。評価ではそのうち 5 個を確かめる。

- **H1**: ワークフローは、エージェント 1 つだけより優れる。
- **H1b**: 同じ費用を与えられたエージェント 1 つよりも優れる。
- **H5**: 2 回目のスキャンの周回でバグが増える。
- **H4**: 懐疑者を置くと、適合率が 0.15 以上上がり、再現率の低下は多くても 0.05 に収まる。
- **H6**: 指摘の失敗する呼び出しを実行すると、懐疑者はより正確になる。

## 環境のセットアップ

空のプロジェクトから始める。パッケージは `jsonschema` の 1 つだけで、あとは OpenAI 互換のエンドポイントがあればよい。

```
uv init dynamic-workflows --python 3.12 && cd dynamic-workflows
uv add jsonschema
export LLM_BASE_URL="https://your-endpoint/v1"   # any OpenAI-compatible server
export LLM_API_KEY="your key"                    # read once, never printed
```

`MODELS gives each role its model, and`PRICE` は 1 回の呼び出しの費用で、単位は**クレジット（credits）**である。最初のコード片は「各ロールにそのモデルを与える」という意味である。

```
"""config.py: the settings every other file reads."""
import json, os
from pathlib import Path

CAP_CREDITS = 1500.0                                     # the cap of a front door given no budget of its own
BASE_URL = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:8000/v1")      # any OpenAI-compatible endpoint
API_KEY = os.environ.get("LLM_API_KEY", "")              # read once from the environment, never printed
MODELS = {"lead": "Qwen/Qwen3.8-Max", "worker": "Qwen/Qwen3.8-27B",        # the code asks for a role, not a model
          "judge": "Qwen/Qwen3.7-Plus", "fast": "Qwen/Qwen3.8-Flash-Next"}
PRICE = {"Qwen/Qwen3.8-Max": 0.5, "Qwen/Qwen3.8-27B": 0.2, "Qwen/Qwen3.7-Plus": 0.2, "Qwen/Qwen3.8-Flash-Next": 0.2}   # credits per call, whatever its length
TEMPERATURE, TOP_P = 0.6, 0.95                           # reasoning models loop under greedy decoding, so we sample
SHARD_TOKENS, CHARS_PER_TOKEN = 100_000, 2.54542         # code per worker call, and characters per token (both measured later)
MAX_AGENTS_PER_RUN = 1000                                # a backstop against a plan that loops forever
DATA = Path("data/algorithms")                           # the library, its planted bugs and the answer key
PROMPTS = json.loads((Path(__file__).parent / "prompts.json").read_text(encoding="utf-8"))      # the instructions, one text per role
```

## 埋め込みバグのベンチマーク

私は 849 個の Python ファイルからなる公開ライブラリを用意し、72 個のファイルにそれぞれバグを 1 つずつ埋め込んだ。各バグは、そのファイルの doctest の例を少なくとも 1 つ失敗させ、失敗させる割合は 40% を超えない。エージェントが読むコピーからは、それらの例を取り除いてある。

![](https://miro.medium.com/v2/resize:fit:6773/1*MLuYp7hOMeqmlsLQ0YDRJw.png)（未取得）

可能な編集から 72 個の埋め込みバグへ（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

- `left out:` 1 行の編集 12 種類、doctest による証明、リークテスト（リポジトリのノートブックにある）

```
"""bench.py: the files, the hidden key and the scorer."""
import ast, functools, json, re

from config import DATA

AUDITED = DATA / "audited"                                    # the copy of the library that agents read
WORK = sorted(p.relative_to(AUDITED).as_posix() for p in AUDITED.rglob("*.py"))     # every file an audit must read
KEY = json.loads((DATA / "hidden" / "answer_key.json").read_text(encoding="utf-8"))   # the 72 planted bugs, in a folder no agent tool opens
```

採点器は、ある行がどの関数に属するかを知っていなければならない。

```
# bench.py
@functools.lru_cache(maxsize=None)
def audited_tree(path):
    # parsed once, then reused
    return ast.parse((AUDITED / path).read_text(encoding="utf-8"))


def function_at(path, line):
    """(name, first line, last line) of the innermost function around a line, or None."""
    best = None

    def walk(node, prefix):
        nonlocal best
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # the innermost function holding the line wins
                if child.lineno <= line <= child.end_lineno and (best is None or child.lineno >= best[1]):
                    best = (prefix + child.name, child.lineno, child.end_lineno)
                walk(child, prefix + child.name + ".")
            else:                                             # methods get their class name
                walk(child, prefix + child.name + "." if isinstance(child, ast.ClassDef) else prefix)
    if path in WORK:                                          # a path a model made up is never opened
        walk(audited_tree(path), "")
    return best
```

指摘が数えられるのは、正しいファイルと関数を挙げ、バグから 5 行以内の位置を指しているときである。

![](https://miro.medium.com/v2/resize:fit:1750/1*AgmbBcCUCjiuCTSZVH_GXg.png)（未取得）

採点器が数えるものと見逃すもの（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

`match` はこれを指摘のリストに適用する。

```
# bench.py
def normalise_path(path):
    # ./x, /x and .../audited/x all mean x
    return re.sub(r"^(\./|/|.*audited/)+", "", re.sub(r"/+", "/", str(path).strip().replace("\\", "/")))


def match(findings, key=KEY, window=5):
    """A finding counts when it names the same file and function as a planted bug, within `window` lines."""
    found, wrong = {}, set()
    for f in findings:
        path, line = normalise_path(f["file"]), int(f.get("line") or 0)
        span = function_at(path, line) if line > 0 else None
        said = f.get("function", "").split(".")[-1]                                # the name the model gave, as a second chance
        hits = [b for b in key if b["path"] == path and abs(line - b["line"]) <= window
                and ((span and span[0] == b["function"]) or (said and said == b["function"].split(".")[-1]))]
        if hits:
            found.setdefault(min(hits, key=lambda b: abs(line - b["line"]))["id"], f)     # the nearest bug wins, and saying it twice counts once
        else:
            wrong.add((path, span[0] if span else f"line {line // 10}"))           # one wrong idea per place, however often repeated
    # recall over the key, precision over what was reported
    tp, fp = len(found), len(wrong)
    return {"found": sorted(found), "recall": tp / len(key), "precision": tp / (tp + fp) if tp + fp else None, "tp": tp, "fp": fp}
```

## 回答をためておく台帳

私はモデルの呼び出しを何度もやり直す。そこで、各回答を質問のフィンガープリントとともに保存し、同じ質問に二度は支払わない。

![](https://miro.medium.com/v2/resize:fit:1750/1*U_YPyRhHKk826vdthnZo8Q.png)（未取得）

フィンガープリントが、その呼び出しが有料かどうかを決める（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

`Reply` は 1 つの回答を保持する。

```
"""llm.py: replies, the ledger, one front door and one budget."""
import hashlib, json, re, sqlite3, threading, time, urllib.request, zlib
from dataclasses import asdict, dataclass

from jsonschema import Draft202012Validator

from config import API_KEY, BASE_URL, CAP_CREDITS, PRICE


@dataclass
class Reply:
    text: str = ""                 # the answer
    finish: str = None             # stop, length or error
    prompt_tokens: int = 0         # as the server counted them
    completion_tokens: int = 0
    seconds: float = 0.0
    model: str = ""
    cached: bool = False           # True when the ledger answered instead of the network


class CacheMiss(RuntimeError):
    """Replay met a question the ledger has never seen."""


class SpendRefused(RuntimeError):
    """A paid call was refused: there is no client to pay with."""
```

`http_client` は、ネットワークに触れる唯一のコードである。

```
# llm.py
def http_client(model, messages, **params):
    """One chat completion over plain HTTP. A failed call raises, so it is never stored."""
    body = json.dumps({"model": model, "messages": messages, **params}).encode()          # the question in chat completions form
    head = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}   # the key travels in a header only
    start = time.perf_counter()
    # one POST, ten minutes at most
    with urllib.request.urlopen(urllib.request.Request(BASE_URL + "/chat/completions", body, head), timeout=600) as r:
        data = json.load(r)
    choice, use = data["choices"][0], data["usage"]          # the answer and the server's token counts
    return Reply(choice["message"].get("content") or "", choice["finish_reason"], use["prompt_tokens"], use["completion_tokens"],
                 time.perf_counter() - start, model)
```

フィンガープリントには**サンプル番号（sample index）**が含まれる。同じ質問のサンプル 0 とサンプル 1 は、互いに独立した回答を得る。

```
# llm.py
class Ledger:
    """Every answer, under a fingerprint of its question."""

    def __init__(self, path):
        # one row per answer, keyed by fingerprint
        self.db, self.lock = sqlite3.connect(str(path), check_same_thread=False), threading.Lock()
        self.db.execute("CREATE TABLE IF NOT EXISTS calls (key TEXT PRIMARY KEY, role, reply BLOB, seconds REAL, credits REAL, created REAL)")

    @staticmethod
    def key(model, messages, params, sample=0):
        blob = json.dumps([model, messages, params, sample], sort_keys=True)     # the question, exactly as it was asked
        return hashlib.sha256(blob.encode()).hexdigest()

    def get(self, key):
        with self.lock:
            row = self.db.execute("SELECT reply FROM calls WHERE key = ?", (key,)).fetchone()
        # stored replies come back marked cached
        return Reply(**{**json.loads(zlib.decompress(row[0])), "cached": True}) if row else None

    def put(self, key, reply, role="", credits=0.0):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO calls VALUES (?,?,?,?,?,?)",
                            (key, role, zlib.compress(json.dumps(asdict(reply)).encode()), reply.seconds, credits, time.time()))
            self.db.commit()                          # a crash loses at most the calls still in flight
```

すべての呼び出しは、`LLM` という 1 つのフロントドア（front door）を通る。

```
# llm.py
class LLM:
    def __init__(self, ledger, mode="collect", client=None, scripted=None, budget=None):
        self.ledger, self.mode, self.client, self.scripted = ledger, mode, client, scripted
        self.budget = budget or Budget(CAP_CREDITS)
```

`chat` は、台帳、リプレイの拒否、無料の代役、予算の順に試し、そのあとで初めてネットワークに出る。

```
# llm.py
    def chat(self, model, messages, *, role="", sample=0, **params):
        key = Ledger.key(model, messages, params, sample)      # the same question always gets the same key
        if hit := self.ledger.get(key):
            return hit                                # free, instant and identical to the first answer
        if self.mode == "replay":
            raise CacheMiss(f"{role or model}: no stored answer, run in collect mode first")
        if self.scripted:                             # a stand-in answers for free and leaves no trace
            return self.scripted(model, messages, dict(params, sample=sample))
        if self.client is None:                       # no client means nothing can be paid for
            raise SpendRefused("no client, so nothing can be collected")
        price = PRICE.get(model, 0.2)
        self.budget.admit(price)                      # may wait here until somebody raises the cap
        try:
            reply = self.client(model, messages, **params)
        except BaseException:
            self.budget.settle(price, 0.0)            # a failed call is not billed and not stored
            raise
        self.budget.settle(price, price)
        self.ledger.put(key, reply, role, price)
        return reply
```

呼び出しを数える偽のクライアントで試す。

```
import time
from config import MODELS
from llm import LLM, Ledger, Reply

paid = []                                           # one entry per call that reaches the "network"
def fake_client(model, messages, **params):         # a stand-in for the network: it answers after a pause
    paid.append(1)
    time.sleep(0.05)
    return Reply('{"answer": "ok"}', "stop", 10, 5, 0.05, model)

llm = LLM(Ledger(":memory:"), client=fake_client)
ask = lambda door, q: door.chat(MODELS["worker"], [{"role": "user", "content": q}], role="demo")
for q in ("what is 2+2?", "name a sorting algorithm", "what is 2+2?"):
    print(f"{q:<26} from the ledger: {ask(llm, q).cached}")
try:
    ask(LLM(llm.ledger, mode="replay", client=fake_client), "a new question")
except Exception as e:
    print(f"{type(e).__name__}: {e}")

#### OUTPUT ####
what is 2+2?               from the ledger: False
name a sorting algorithm   from the ledger: False
what is 2+2?               from the ledger: True
CacheMiss: demo: no stored answer, run in collect mode first
```

繰り返しの呼び出しは台帳から無料で返り、リプレイでは、ネットワークに触れることなく `CacheMiss` が発生した。

## シャードパッカー

課金は呼び出し単位なので、大きなシャードは安く見える。しかし、モデルは長い入力の冒頭より先にある細部を見落とすことがある。**シャード（shard）**とは、1 人のワーカーが 1 回の呼び出しで読むコードである。`numbered` は行番号を付け、`TOKENS` は、ワーカーから見える形で各ファイルの大きさを測る。

```
"""shards.py: numbered lines, packed into shards."""
from bench import AUDITED, WORK
from config import CHARS_PER_TOKEN


def numbered(path):
    lines = (AUDITED / path).read_text(encoding="utf-8").split("\n")
    # a path header, then numbered lines
    return f"### {path}\n" + "\n".join(f"{i:>5}| {ln}" for i, ln in enumerate(lines, 1))


TOKENS = {p: int(len(numbered(p)) / CHARS_PER_TOKEN) for p in WORK}      # each file's size as a worker sees it
```

`pack` は、次のファイルが収まらなくなるまで、ファイル全体を単位としてシャードに詰める。

```
# shards.py
def pack(paths, target):
    """Whole files packed into shards of about `target` tokens, first fit."""
    shards, sizes = [], []
    # folder by folder, biggest files first
    for folder in sorted({p.split("/")[0] for p in paths}):
        for p in sorted((q for q in paths if q.split("/")[0] == folder), key=lambda q: -TOKENS[q]):
            # the first shard with room takes the file
            for i, size in enumerate(sizes):
                if size + TOKENS[p] <= target:
                    shards[i].append(p)
                    sizes[i] += TOKENS[p]
                    break
            else:                                    # no room anywhere: start a new shard
                shards.append([p])
                sizes.append(TOKENS[p])
    return shards
```

事前に固定した私の規則は、最良の再現率から 0.05 以内で最も大きいサイズを選ぶというもので、24 個のバグが埋め込まれた 283 ファイルでは 100,000 トークンが選ばれた。のちのシステム全体のテストはこれと食い違った。スリムな計画は、20,000 トークンのシャードでバグの 0.38 を見つけ、100,000 トークンでは 0.18 だった。

![](https://miro.medium.com/v2/resize:fit:6283/1*yo2hXoPF0gbMZ4CMAcC_QQ.png)（未取得）

14 個のシャードと、2 つのシャードサイズのテスト（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

以下で比べるワークフローは、すべて 100,000 トークンのシャードを使った。

## ワーカースレッドとイベントストリーム

**ラン（run）**は計画の 1 回の実行であり、計画は、ランを受け取る Python の関数である。

```
"""runtime.py: workers, threads, events, phases and background runs."""
import collections, concurrent.futures as cf, threading, time
from dataclasses import dataclass, field

from config import MAX_AGENTS_PER_RUN, MODELS, PRICE, TEMPERATURE, TOP_P
from llm import CacheMiss, SpendRefused, extract_json, validate


class RunCancelled(RuntimeError):
    """The run was cancelled."""


ABORT = (RunCancelled, SpendRefused, CacheMiss)    # only these end a run, other failures stay with the worker
```

各ワーカーは、その会話の全体である**スレッド（thread）**を残す。

```
# runtime.py
@dataclass
class Thread:
    """One worker's whole conversation, kept so a person can read it afterwards."""
    id: str
    phase: str
    label: str                                     # what the plan called it, such as "scan:logic:maths#3"
    model: str
    role: str = "worker"
    messages: list = field(default_factory=list)   # everything the worker was sent
    replies: list = field(default_factory=list)    # every Reply it got back
    status: str = "waiting"                        # waiting, running, done or failed
    started: float = 0.0                           # seconds since the run began
    ended: float = 0.0
    cost: float = 0.0                              # credits charged for its paid calls
    result: object = None
    error: str = None
```

`Run keeps everything a run leaves.`（ランが残すものをすべて保持する、の意）

```
# runtime.py
class Run:
    def __init__(self, title, goal="", *, llm, run_id=None, concurrency=16, max_agents=MAX_AGENTS_PER_RUN):
        self.title, self.goal, self.llm, self.run_id = title, goal, llm, run_id or title.lower().replace(" ", "-")
        self.t0, self.max_agents, self.lock = time.perf_counter(), max_agents, threading.Lock()
        # slots cap concurrency, cancelled refuses new workers
        self.slots, self.cancelled = threading.BoundedSemaphore(concurrency), threading.Event()
        # what a person reads afterwards
        self.threads, self.phases, self.events, self.dropped, self.current = [], [], [], [], None
        self.status, self.result, self.error, self._worker = "created", None, None, None

    def elapsed(self):
        return time.perf_counter() - self.t0

    def emit(self, kind, **data):
        self.events.append({"t": round(self.elapsed(), 3), "type": kind, **data})      # the run's stream: every event, in order
```

**フェーズ（phase）**は、Scan や Verify のように名前の付いた、ランの一区間である。

```
# runtime.py
    def phase(self, title):
        with self.lock:
            if self.current:                       # closing a phase records its workers and time
                mine = [t for t in self.threads if t.phase == self.current["name"]]
                self.emit("run.phase_ended", phase=self.current["name"], agents=len(mine), seconds=round(self.elapsed() - self.current["started"], 2))
            self.current = {"name": title, "started": self.elapsed()} if title else None
            if self.current:
                self.phases.append(self.current)
                self.emit("run.phase_started", phase=title, index=len(self.phases))

    def log(self, message):
        self.emit("run.log", message=str(message)[:500])
```

`_new_thread` は、暴走を防ぐ最後の歯止めも担う。

```
# runtime.py
    def _new_thread(self, label, model, phase, role):
        """The next worker's thread, or None when the worker limit is reached."""
        with self.lock:
            if len(self.threads) >= self.max_agents:                      # over the limit: record what was refused
                self.dropped.append(label)
                self.emit("run.dropped", label=label, limit=self.max_agents)
                if len(self.dropped) >= self.max_agents:                  # asking for twice the limit is treated as a runaway
                    self.log(f"the plan asked for {2 * self.max_agents} workers, twice its limit: cancelled as a runaway")
                    self.cancelled.set()
                return None
            t = Thread(f"{self.run_id}/t{len(self.threads) + 1:03d}", phase or (self.current["name"] if self.current else ""),
                       label or "worker", MODELS.get(model, model), role)
            self.threads.append(t)
            return t
```

`agent()` は 1 人のワーカーを起動し、検査済みの値か `None` を返す。

```
# runtime.py
    def agent(self, prompt="", *, schema=None, model="worker", label="", system="", data=None, sample=0, role="worker", phase=None):
        """One worker: its checked JSON answer, or None. Only an exception that must end the whole run gets out."""
        if self.cancelled.is_set():
            raise RunCancelled(self.run_id)
        t = self._new_thread(label, model, phase, role)
        if t is None:
            return None
        self.emit("run.agent_started", thread=t.id, label=t.label, phase=t.phase)
        with self.slots:                           # at most `concurrency` workers talk at the same time
            t.started, t.status = self.elapsed(), "running"
            try:
                t.result = self._converse(t, system, (prompt + "\n\n" + (data or "")).strip(), schema, sample)
                t.status = "done" if t.result is not None else "failed"
            except ABORT:
                t.status = "failed"
                raise
            except Exception as e:                 # any other failure stays the worker's own
                t.status, t.error = "failed", f"{type(e).__name__}: {e}"[:300]
            finally:
                t.ended = self.elapsed()
        self.emit("run.agent_ended", thread=t.id, label=t.label, phase=t.phase, ok=t.status == "done", credits=round(t.cost, 2),
                  seconds=round(t.ended - t.started, 2), cached=bool(t.replies) and all(r.cached for r in t.replies))
        return t.result
```

まず、返信から JSON を取り出す。

```
# llm.py
def extract_json(text):
    """The first JSON object in a reply, even inside a code fence."""
    t = re.sub(r"^`{3}[a-zA-Z]*\s*|\s*`{3}$", "", text.strip())     # `{3} is three backticks
    for start in [i for i, c in enumerate(t) if c == "{"]:
        try:
            return json.JSONDecoder().raw_decode(t[start:])[0]
        except ValueError:
            continue
```

`validate` は、スキーマの誤りを、モデルが直せる短い行に変える。

```
# llm.py
def validate(obj, schema):
    if obj is None:
        return ["the reply is not a JSON object"]
    # at most eight short problems the model can fix
    errors = sorted(Draft202012Validator(schema).iter_errors(obj), key=lambda e: list(e.path))
    return [f"{'/'.join(map(str, e.path)) or 'top level'}: {e.message[:120]}" for e in errors[:8]]
```

ワーカーの会話は、多くても 2 ターンである。

![](https://miro.medium.com/v2/resize:fit:1750/1*dTZuYIqQ8xpXWbyW6dBwng.png)（未取得）

2 ターンで終わる 1 人のワーカーの会話（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

それらのターンは `_converse` の中にある。

```
# runtime.py
    def _converse(self, t, system, user, schema, sample):
        params = {"temperature": TEMPERATURE, "top_p": TOP_P, "max_tokens": 16000}
        if schema is not None:
            params["response_format"] = {"type": "json_object"}      # JSON mode when the plan wants a schema
        if t.model == MODELS["worker"] or t.role == "scan":
            params["enable_thinking"] = False      # thinking doubled recall but took 50 times as long
        t.messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
        for turn in range(2):                      # the first answer, then at most one repair
            r = self.llm.chat(t.model, t.messages, role=t.role, sample=sample, **params)
            t.replies.append(r)
            t.cost += 0 if r.cached else PRICE.get(t.model, 0.2)
            obj = r.text if schema is None else extract_json(r.text)
            errors = [] if schema is None else validate(obj, schema)
            if not errors:
                return obj
            # the repair turn lists the problems
            t.messages += [{"role": "assistant", "content": r.text[:6000]},
                           {"role": "user", "content": "Your answer does not match the schema:\n- " + "\n- ".join(errors)
                            + "\nSend the corrected JSON object only."}]
        t.error = "schema: " + " | ".join(errors)[:240]
```

`run_sync` は計画の全体を実行する。

```
# runtime.py
    def run_sync(self, plan):
        self.status = "running"
        self.emit("run.created", title=self.title)
        try:
            self.result = plan(self)
            self.status = "completed"
        except RunCancelled:
            self.status = "cancelled"
        except Exception as e:                     # includes the aborts that end a run
            self.status, self.error = "failed", f"{type(e).__name__}: {e}"[:300]
        finally:                                   # always close the last phase
            self.phase(None)
            self.emit("run.ended", status=self.status, seconds=round(self.elapsed(), 2), agents=len(self.threads),
                      credits=round(sum(t.cost for t in self.threads), 2))
        return self.result
```

`parallel` は、引数のない関数であるサンク（thunk）をすべて同時に実行する。これは**バリア（barrier）**であり、最も遅いものが終わったときに戻る。

![](https://miro.medium.com/v2/resize:fit:5950/1*wLhuh7vG7pcX2G3Vtdo18Q.png)（未取得）

終わったワーカーは、最も遅いものを待つ（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

固定計画のあるスキャンフェーズでは、終わったワーカーが最も遅いものを待った時間は、ワーカー換算で 37 分に達した。

```
# runtime.py
    def parallel(self, thunks):
        thunks = list(thunks)
        out, aborts = [None] * len(thunks), []
        # one task per thunk, up to 64 threads
        with cf.ThreadPoolExecutor(max(1, min(len(thunks), 64))) as pool:
            futures = {pool.submit(fn): i for i, fn in enumerate(thunks)}
            for f in cf.as_completed(futures):
                try:
                    out[futures[f]] = f.result()      # results keep the order of the thunks
                except ABORT as e:
                    aborts.append(e)
                    self.cancelled.set()           # stop the work that has not started yet
                except Exception as e:
                    self.log(f"a parallel task failed: {type(e).__name__}: {e}")
        if aborts:                                 # the first abort ends the phase for everyone
            raise aborts[0]
        return out
```

偽のクライアント上の 1 人のワーカーで、ランが記録するイベントを示す。

```
from runtime import Run

SCHEMA = {"type": "object", "required": ["answer"]}
run = Run("one worker", llm=llm)
run.run_sync(lambda r: (r.phase("Scan"), r.agent("hello", schema=SCHEMA, label="scan#0"))[1])
t = run.threads[0]
print([e["type"][4:] for e in run.events])
print(f"{t.id} | {t.phase} | {t.label} | {t.status} | {t.cost} credits | {len(t.replies)} reply")

#### OUTPUT ####
['created', 'phase_started', 'agent_started', 'agent_ended', 'phase_ended', 'ended']
one-worker/t001 | Scan | scan#0 | done | 0.2 credits | 1 reply
```

ライブラリ上の実際のワーカーは、100,911 トークンを読み、18.7 秒かかった。

## セッション予算と復旧

すべてのワーカーは 1 つのメーターから支払う。上限に達すると、人が上限を引き上げるまでワーカーは待つ。

![](https://miro.medium.com/v2/resize:fit:6689/1*pZoBYPzkNVQl5TsbFiMyVQ.png)（未取得）

支出は上限で一時停止し、その後再開する（作成: @fareedkhandev）

`admit` はまず、呼び出しの価格を確保する。

```
# llm.py
class Budget:
    def __init__(self, cap):
        # spent is billed, reserved is held for calls in flight
        self.cap, self.spent, self.reserved, self.paused = float(cap), 0.0, 0.0, False
        self.cond = threading.Condition()

    def admit(self, cost):
        with self.cond:                               # reserve the price, or wait here until the cap is raised
            while self.spent + self.reserved + cost > self.cap + 1e-9:
                self.paused = True
                self.cond.wait(timeout=1.0)
            self.paused = False
            self.reserved += cost
```

`settle` はそれを課金し、`raise_to` は上限を引き上げる。

```
# llm.py
    def settle(self, reserved, actual):
        with self.cond:                               # a reservation becomes spending, or is released if the call was not billed
            self.reserved -= reserved
            self.spent += actual
            self.cond.notify_all()

    def raise_to(self, cap):
        with self.cond:                               # raising the cap wakes every waiting worker
            self.cap, self.paused = float(cap), False
            self.cond.notify_all()
```

`start` は、長い計画を専用のスレッドで実行する。

```
# runtime.py
    def start(self, plan):
        # the plan runs on its own thread
        self._worker = threading.Thread(target=self.run_sync, args=(plan,), daemon=True)
        self._worker.start()
        return self

    def wait(self):
        self._worker.join()                        # block until the plan has finished
        return self.result

    def cancel(self):
        self.cancelled.set()                       # workers already talking finish, new ones are refused
```

`statusline` は、どのスレッドからでも「進み具合はどうか」に答える。

```
# runtime.py
    def statusline(self):
        """One line answering 'how is it going?' from any thread."""
        n = collections.Counter(t.status for t in self.threads)
        return (f"{self.run_id} | {self.status} | phase {len(self.phases)}: {self.current['name'] if self.current else '-'} | "
                f"{n['running']} running, {n['done']} done, {n['failed']} failed | {sum(t.cost for t in self.threads):.1f} credits | "
                f"{self.elapsed():.1f}s" + (" | PAUSED at the budget" if self.llm.budget.paused else ""))
```

40 人のワーカーに上限 5 クレジットを与える。1 回 0.2 クレジットなら 25 回の呼び出しに足りる。

```
from llm import Budget

paid.clear()
capped = LLM(Ledger(":memory:"), client=fake_client, budget=Budget(5.0))
run = Run("forty workers", llm=capped, concurrency=10)
run.start(lambda r: r.parallel([lambda i=i: r.agent(f"question {i}", schema=SCHEMA) for i in range(40)]))
time.sleep(1.2)
print(f"requests sent {len(paid)}\n{run.statusline()}")
capped.budget.raise_to(10.0)
run.wait()
print(f"cap raised to {capped.budget.cap}: {run.status}, spent {capped.budget.spent:.1f}, requests sent {len(paid)}")

#### OUTPUT ####
requests sent 25
forty-workers | running | phase 0: - | 10 running, 25 done, 0 failed | 5.0 credits | 1.2s | PAUSED at the budget
cap raised to 10.0: completed, spent 8.0, requests sent 40
```

ランはちょうど 25 件のリクエストで止まり、上限を引き上げたあとは 40 件で完了した。次に、2 フェーズのランを途中の半ばでキャンセルし、同じ台帳を使って同じ計画をもう一度実行する。

```
plan = lambda r: (r.parallel([lambda i=i: r.agent(f"scan {i}", schema=SCHEMA, phase="Scan") for i in range(30)]),
                  r.parallel([lambda i=i: r.agent(f"verify {i}", schema=SCHEMA, model="judge", phase="Verify") for i in range(30)]))
paid.clear()
ledger = Ledger(":memory:")
first = Run("crash", llm=LLM(ledger, client=fake_client), concurrency=8).start(plan)
while len(paid) < 25:                                  # let it get about halfway, then pull the plug
    time.sleep(0.01)
first.cancel()
first.wait()
before = len(paid)
second = Run("crash", llm=LLM(ledger, client=fake_client), concurrency=8)
second.run_sync(plan)
print(f"first run {first.status} after {before} paid calls, then the second run {second.status} with {len(paid) - before} new calls, {len(paid)} in all")

#### OUTPUT ####
first run cancelled after 30 paid calls, then the second run completed with 30 new calls, 60 in all
```

この計画は、中断されてもされなくても 60 回の呼び出しを必要とし、同じ呼び出しに二度支払うことはなかった。

## 監査タスクキット

キットのうち 3 つのステップがモデルを呼ぶ。`scan` は 1 人のワーカーに 1 つのシャードと 1 つの**レンズ（lens）**を与え、`check gives a skeptic a batch, and`report` はリストを書く。2 つ目のコード片は「懐疑者にバッチを与える」という意味である。

![](https://miro.medium.com/v2/resize:fit:6178/1*bixNeZhHUxKSrgyOZvbQPA.png)（未取得）

監査キットを流れるもの（作成: @fareedkhandev）

**懐疑者（skeptic）**には、報告の大半は誤検知であること、確信が持てないときは `real: false` と答えることを伝える。

```
"""kit.py: the words of an audit: scan, check, vote and report."""
import collections

from bench import WORK, function_at, normalise_path
from config import MODELS, PROMPTS, SHARD_TOKENS
from shards import numbered, pack

LENSES = ["boundaries", "logic", "state"]                 # a lens points a worker at one family of mistakes, "general" at none
FINDINGS = {"type": "object", "required": ["findings"], "properties": {"findings": {"type": "array", "items": {
    "type": "object", "required": ["file", "line", "claim"], "properties": {"line": {"type": "integer"}}}}}}
VERDICTS = {"type": "object", "required": ["verdicts"], "properties": {"verdicts": {"type": "array", "items": {
    "type": "object", "required": ["report", "real"], "properties": {"real": {"type": "boolean"}}}}}}
REPORT = {"type": "object", "required": ["bugs"], "properties": {"bugs": {"type": "array", "items": {"type": "object", "required": ["ids"]}}}}
```

`batches cuts a list into groups, and`flatten` はリストを 1 つに戻す。最初のコード片は「リストをグループに切り分ける」という意味である。

```
# kit.py
def batches(items, size):
    items, size = list(items), max(1, int(size))
    return [items[i:i + size] for i in range(0, len(items), size)]


def flatten(lists):
    return [x for xs in lists if xs for x in xs]           # one list from a list of lists, skipping workers that failed (None)
```

`finding` は 1 つの指摘を作り、`key_of` はその場所に名前を付ける。

```
# kit.py
def finding(obj, source=""):
    path, line, conf = normalise_path(obj.get("file", "")), int(obj.get("line") or 0), obj.get("confidence")
    span = function_at(path, line)                         # models often name the wrong function
    # texts are cut to keep prompts small
    return {"file": path, "line": line, "function": span[0] if span else str(obj.get("function") or ""), "source": source,
            "claim": str(obj.get("claim") or "")[:400], "failing_call": str(obj.get("failing_call") or "")[:400],
            "expected": str(obj.get("expected") or "")[:200], "confidence": min(1.0, max(0.0, float(conf))) if isinstance(conf, (int, float)) else 0.5}


def key_of(f):
    """The place a finding is about: its file and function, or its file and ten-line block."""
    return f"{f['file']}::{f['function']}" if f["function"] else f"{f['file']}::line {f['line'] // 10 * 10}"
```

`dedupe merges findings about one place and counts the workers behind them.`（同じ場所についての指摘をまとめ、その背後にいるワーカーの数を数える、の意）

```
# kit.py
def dedupe(findings):
    # group by place, keep the most confident
    groups = collections.defaultdict(list)
    for f in findings:
        groups[key_of(f)].append(f)
    return [dict(max(g, key=lambda f: (f["confidence"], -f["line"], f["claim"], f["failing_call"], f["source"])),   # ties are broken by
                 reports=sum(f.get("reports", 1) for f in g)) for _, g in sorted(groups.items())]                 # content, so every run keeps the same one
```

場所が残るのは、十分な数の懐疑者がそれを本物と判定したときだけであり、それを調べるのが `vote` である。

```
# kit.py
def vote(candidates, verdicts, need=2):
    # keep places that at least `need` skeptics called real
    real = collections.Counter(v["key"] for v in verdicts if v and v.get("real") is True)
    return [dict(c, votes=real[key_of(c)]) for c in candidates if real[key_of(c)] >= need]
```

懐疑者が読むものは `reports` から作られ、指摘 1 件につき 1 ブロックになる。

```
# kit.py
def reports(batch):
    blocks = []
    for i, f in enumerate(batch, 1):
        name, first, last = function_at(f["file"], f["line"]) or ("", f["line"] - 15, f["line"] + 15)
        if last - first > 60:                              # a very long function: a window around the line instead
            first, last = f["line"] - 15, f["line"] + 15
        code = "\n".join(numbered(f["file"]).split("\n")[max(1, first):last + 1]) if f["file"] in WORK else "(no such file)"
        # one block per finding, with its code
        blocks.append(f"--- report {i} ---\nfile: {f['file']}\nfunction: {f['function'] or '(none)'}\nline: {f['line']}\nclaim: {f['claim']}\n"
                      f"failing call: {f['failing_call'] or '(none given)'}\nexpected by the finder: {f['expected'] or '(not given)'}\ncode:\n{code}")
    return "\n\n".join(blocks)
```

`AuditKit` は各ステップを 1 つのランに結び付ける。ラン `r` はサンプル番号を `100 * r` ずつずらすので、3 回のランは互いに独立にサンプリングされる。

```
# kit.py
class AuditKit:
    def __init__(self, run, number=0):
        self.run, self.offset = run, 100 * number          # run r uses sample indexes 100 r, 100 r + 1, ...

    def scan(self, shard, lens="general", sample=0, model="worker"):
        # a lens adds a paragraph, the shard is numbered code
        label = f"scan:{lens}:{shard[0].split('/')[0]}#{sample}"
        obj = self.run.agent(system=PROMPTS["scan"] + (f"\n\n{PROMPTS['lens_' + lens]}" if lens in LENSES else ""), schema=FINDINGS,
                             data="\n\n".join(map(numbered, shard)), model=model, role="scan", label=label, sample=self.offset + sample)
        return [finding(f, label) for f in (obj or {}).get("findings", []) if isinstance(f, dict)]

    def check(self, batch, sample=0, model="judge"):
        batch = [f for f in batch if f][:8]           # a skeptic reads at most eight findings at once
        obj = batch and self.run.agent(system=PROMPTS["skeptic"], data=reports(batch), schema=VERDICTS, model=model, role="skeptic",
                                       label=f"check:{batch[0]['file'].split('/')[0]}#{sample}", sample=self.offset + sample)
        # match verdicts to findings by number
        said = {v.get("report"): v for v in (obj or {}).get("verdicts", []) if isinstance(v, dict)}
        return [{"key": key_of(f), "real": said.get(i, {}).get("real"), "reason": str(said.get(i, {}).get("reason", ""))[:200]}
                for i, f in enumerate(batch, 1)]
```

`names` は、計画が呼び出してよいものを列挙する。

```
# kit.py
    def report(self, confirmed, model="lead"):
        # one line per confirmed finding
        rows = "\n".join(f"C{i} | {f['file']}:{f['line']} | {f['function'] or '-'} | {f['votes']} votes | {f['claim'][:160]}"
                         for i, f in enumerate(confirmed, 1))
        obj = (confirmed and self.run.agent(system=PROMPTS["report"], data=rows, schema=REPORT, model=model, role="report", label="report",
                                            sample=self.offset)) or {}
        rank = {i: g.get("severity", "unranked") for g in obj.get("bugs", []) for i in g["ids"]}      # the severity the report gave each id
        bugs = [dict(f, severity=rank.get(f"C{i}", "unranked")) for i, f in enumerate(confirmed, 1)]   # a finding the writer forgot is added back
        return {"bugs": bugs, "summary": str(obj.get("summary", ""))[:600], "left_out": sum(f"C{i}" not in rank for i in range(1, len(confirmed) + 1))}

    def names(self):
        run, budget = self.run, self.run.llm.budget       # everything a plan may call
        return {"agent": lambda prompt="", **kw: run.agent(prompt, **dict(kw, sample=self.offset + kw.get("sample", 0))),
                "parallel": run.parallel, "phase": run.phase, "log": run.log, "budget": lambda: round(budget.cap - budget.spent - budget.reserved, 2),
                "work": list(WORK), "shards": lambda tokens=SHARD_TOKENS: pack(WORK, int(tokens)), "batches": batches, "flatten": flatten,
                "render": lambda shard: "\n\n".join(map(numbered, shard)), "dedupe": dedupe, "key_of": key_of, "scan": self.scan,
                "check": self.check, "vote": vote, "report": self.report, "LENSES": list(LENSES), "MODELS": sorted(MODELS),
                "SCHEMAS": {"findings": FINDINGS, "verdicts": VERDICTS}}
```

### 固定のベースライン

まず、上回るべき計画が必要である。3 つのレンズすべてですべてのシャードをスキャンし、各指摘を 3 人の懐疑者で確かめ、2 人が確認したものを残す、というものである。

```
"""plans.py: a fixed plan, the whitelist, the dry run and the gate."""
import ast, builtins, collections, hashlib, json, re, threading, zlib

from config import PRICE
from kit import AuditKit
from llm import LLM, Budget, Ledger, Reply
from runtime import Run

FIXED_PROGRAM = """phase("Scan")
found = flatten(parallel([lambda s=s, lens=lens: scan(s, lens) for s in shards(100000) for lens in LENSES]))
candidates = dedupe(found)
phase("Verify")
verdicts = flatten(parallel([lambda b=b, k=k: check(b, sample=k) for b in batches(candidates, 6) for k in range(3)]))
confirmed = vote(candidates, verdicts, need=2)
phase("Report")
result = report(confirmed)"""
```

3 回のランで、この計画は 72 個のバグのうち 20 個、23 個、22 個を見つけ、再現率は 0.28、0.32、0.31 だった。費用は 1 回あたり約 14 クレジットである。

## 制限された計画の言語

私たちの固定計画は決して変わらない。それでも、その記録を見ると、2 周目と 3 周目では、1 周目が見逃した 9 個の埋め込みバグが見つかっている。より良い計画は、1 周で増える分が小さくなるまでスキャンを続け、`budget()` が少なくなれば縮む。設定のリストではそれを表現できないので、リードは Python を書く。

これは、実行前に検査でき、与えられた名前にしか届かない、制限付きの Python である。この制限は、それぞれが 1 つのことを禁じる規則からなる**ホワイトリスト（whitelist）**である。計画は私たち自身のリードから来るので、これはセキュリティの境界ではない。

```
# plans.py
ALLOWED = {getattr(ast, n) for n in (            # the only kinds of syntax a plan may use
    "Module Expr Assign AugAssign For If Break Continue Return FunctionDef Lambda ListComp DictComp SetComp GeneratorExp comprehension "
    "Call keyword Name Attribute Subscript Slice Constant List Tuple Dict Set BoolOp BinOp UnaryOp Compare IfExp JoinedStr FormattedValue "
    "arguments arg Starred Load Store And Or Add Sub Mult Div FloorDiv Mod Not USub UAdd Eq NotEq Lt LtE Gt GtE In NotIn Is IsNot").split()}
WHY_NOT = {ast.While: "use a for loop over range(n), so the loop states its bound", ast.Import: "a plan has nothing to import",
           ast.Try: "a plan must not hide errors, and failed workers already return None"}
METHODS = {"append", "extend", "get", "items", "keys", "values", "update", "add", "setdefault", "pop", "sort", "split", "strip", "lower", "upper",
           "join", "startswith", "endswith", "count", "index", "replace"}      # the methods a plan may call on data, with format left out on purpose
BUILTINS = ["len", "range", "enumerate", "zip", "sorted", "min", "max", "sum", "any", "all", "list", "dict", "set", "tuple", "str", "int",
            "float", "round", "abs"]


class PlanRejected(ValueError):
    """A plan program failed the whitelist check or the dry run."""
```

規則 2 と規則 4 は構文を検査する。

```
# plans.py
def rule_syntax(tree):
    """Rules 2 and 4: only the allowed syntax, no number above a million, and attributes only as calls of a few methods."""
    # called attributes, so a bare one stands out
    called, out = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}, []
    for n in ast.walk(tree):
        line = getattr(n, "lineno", 1)
        if type(n) not in ALLOWED:                                # rule 2: syntax outside the list
            out.append(f"line {line}: {type(n).__name__} is not allowed: {WHY_NOT.get(type(n), 'it is not part of the plan language')}")
        # rule 2 again: a number no plan needs
        elif isinstance(n, ast.Constant) and type(n.value) is int and abs(n.value) > 1_000_000:
            out.append(f"line {line}: the number {n.value} is larger than any plan needs")
        # rule 4: only allowed method calls
        elif isinstance(n, ast.Attribute) and (n.attr.startswith("_") or id(n) not in called or n.attr not in METHODS):
            out.append(f"line {line}: '.{n.attr}' is not allowed: a plan may only call {', '.join(sorted(METHODS))} on data")
    return out
```

規則 3 はすべての名前を検査する。

```
# plans.py
def rule_names(tree, names):
    """Rule 3: only the given names. None starts with an underscore, and the language itself cannot be reassigned."""
    # names the plan binds itself
    bound = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    bound |= {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)} | {n.arg for n in ast.walk(tree) if isinstance(n, ast.arg)}
    out = []
    for n in ast.walk(tree):
        name = n.id if isinstance(n, ast.Name) else n.name if isinstance(n, ast.FunctionDef) else n.arg if isinstance(n, ast.arg) else None
        stored = not isinstance(n, ast.Name) or isinstance(n.ctx, ast.Store)
        if name is None:
            continue
        if name.startswith("_") and name != "_":                  # a lone _ is the usual name for an unused value
            out.append(f"line {n.lineno}: the name '{name}' starts with an underscore, which is not allowed")
        elif name in names and stored:
            out.append(f"line {n.lineno}: '{name}' is part of the plan language and cannot be reassigned")
        # a name it reads must be defined
        elif not stored and name not in names | set(BUILTINS) | bound:
            out.append(f"line {n.lineno}: the name '{name}' is not defined: the plan language has no such name")
    return sorted(set(out), key=lambda s: int(s.split(":")[0][5:]))
```

規則 1 は計画を短く保ち、規則 5 は計画に `result` を代入するよう求める。

```
# plans.py
def check_program(src, names):
    """Every problem with a plan program, by line. An empty list means it may go on."""
    if len(src) > 6000 or len(src.splitlines()) > 80:             # rule 1: short enough to read in one sitting
        return [f"line 1: the program has {len(src.splitlines())} lines and {len(src)} characters, and the limit is 80 and 6,000"]
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"line {e.lineno}: this is not valid Python ({e.msg})"]
    has_result = any(isinstance(n, ast.Name) and n.id == "result" and isinstance(n.ctx, ast.Store) for n in ast.walk(tree))   # rule 5: the plan sets result
    # rules 2, 3 and 4 walk the syntax tree
    return rule_syntax(tree) + rule_names(tree, set(names)) + ([] if has_result else ["line 1: the program never assigns `result`"])
```

`run_program` は、計画が検査を通ったあとにだけそれを実行する。手の届くのはキットと少数の組み込み関数だけである。

```
# plans.py
def run_program(src, kit):
    problems = check_program(src, kit.names())
    if problems:
        raise PlanRejected(" | ".join(problems[:5]))
    # only the kit's names and safe built-ins
    env = dict(kit.names(), __builtins__={n: getattr(builtins, n) for n in BUILTINS})
    exec(compile(src, f"<plan {kit.run.run_id}>", "exec"), env)
    return env.get("result")
```

検査器は、私が書いた 14 個の悪意あるプログラムをすべて拒否し、そのたびに、モデルが対処できる理由を付けた。

![](https://miro.medium.com/v2/resize:fit:6437/1*jWiR7IH2mqPx7L-tb5EUdg.png)（未取得）

計画が費用を使う前の 5 つの検査（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

## ドライランと承認ゲート

計画はすべての規則を通っても、費用が高くなることがある。起動するワーカーの数が、先に動いたワーカーが返す内容に左右されるからである。**ドライラン（dry run）**は、即座に答えて費用がかからない代役のモデルを相手に、計画を書かれたとおりに実行する。

```
# plans.py
def blind(model, messages, params):
    system, text = messages[0]["content"], messages[-1]["content"]
    # answers come from a hash of the question
    seed = zlib.crc32((text[:300] + str(params.get("sample", 0))).encode())
    if system.startswith("You are reviewing"):
        paths = re.findall(r"^### (\S+)$", text, re.M) or ["unknown.py"]
        answer = {"findings": [{"file": paths[(seed + 7 * j) % len(paths)], "line": 5 + (seed >> (j % 16)) % 60, "claim": "a made-up finding",
                                "confidence": 0.5} for j in range(seed % 3)]}          # none, one or two findings per call
    elif system.startswith("You check"):
        seed = zlib.crc32((text[:200] + str(params.get("sample", 0))).encode())
        answer = {"verdicts": [{"report": i, "real": (seed >> i) % 5 < 2} for i in range(1, len(re.findall(r"^--- report \d+ ---$", text, re.M)) + 1)]}
    else:                                                         # the report: every finding in a group of its own
        answer = {"bugs": [{"ids": [i], "severity": "medium"} for i in re.findall(r"^(C\d+) \|", text, re.M)], "summary": "a made-up report"}
    return Reply(json.dumps(answer), "stop", model=model)
```

`dry_run` は、プログラムがしたことを実際の価格で見積もり、実行時間には時間制限がかかる。

```
# plans.py
def dry_run(src, budget=150, timeout=60):
    llm = LLM(Ledger(":memory:"), scripted=blind, budget=Budget(budget))          # budget() starts where the real run starts
    run = Run("dry run", llm=llm, run_id="dry-" + hashlib.sha256(src.encode()).hexdigest()[:8], concurrency=64)
    kit = AuditKit(run)
    problems = check_program(src, kit.names())
    if problems:
        return None, problems
    worker = threading.Thread(target=lambda: run.run_sync(lambda r: run_program(src, kit)), daemon=True)
    worker.start()
    worker.join(timeout)
    if worker.is_alive():                                         # a clock bounds the running time, which no rule can check
        run.cancel()
        return None, [f"line 1: the dry run did not finish within {timeout} s, so the plan probably loops without end"]
    if run.status != "completed":
        return None, [f"line 1: the dry run ended {run.status}: {run.error or f'{len(run.dropped)} workers refused by the agent limit'}"]
    # price the calls at the real prices
    calls = collections.Counter(t.model for t in run.threads for _ in t.replies)
    return {"agents": len(run.threads), "calls": sum(calls.values()), "credits": round(sum(PRICE.get(m, 0.2) * n for m, n in calls.items()), 1),
            "phases": {p["name"]: sum(t.phase == p["name"] for t in run.threads) for p in run.phases}}, []
```

**承認ゲート（approval gate）**は、どの計画も見積もる前に書いておいた方針を適用する。40 クレジット以下で、予算の 3 分の 1 以下の計画は、自動で通る。

```
# plans.py
AUTO_APPROVE = {"max_credits": 40.0, "max_share": 1 / 3}         # the policy, written down before any plan is priced


def approve(est, budget, person=None):
    if est is None:                                               # a plan that failed its checks never runs
        return "refused", "the plan failed its check or its dry run"
    if est["credits"] > budget:                                   # nor one costing more than the budget
        return "refused", f"estimated {est['credits']:.1f} credits is more than the whole budget of {budget:.0f}"
    limit, cost = min(AUTO_APPROVE["max_credits"], AUTO_APPROVE["max_share"] * budget), f"estimated {est['credits']:.1f} credits"
    if est["credits"] <= limit:
        return "approved", f"{cost} is under the automatic limit of {limit:.1f}"
    if person is None:                                            # above the limit a person decides, or the plan waits
        return "held", f"{cost} is over the automatic limit of {limit:.1f}, so a person must approve it"
    yes = bool(person(est))
    return ("approved" if yes else "refused"), f"a person {'approved' if yes else 'refused'} it after reading the {cost}"
```

私は 3 つの計画を見積もった。固定計画、`budget()` が少なくなると縮む計画、そして、すべての規則を通るのに 100 万人のワーカーを要求する暴走計画である。

```
from kit import AuditKit
from plans import FIXED_PROGRAM, approve, check_program, dry_run

names = AuditKit(Run("api", llm=llm)).names()

FIT = """lenses = LENSES if budget() > 100 else ["general"]
skeptics = 3 if budget() > 100 else 1
found = dedupe(flatten(parallel([lambda s=s, l=l: scan(s, l) for s in shards(40000) for l in lenses])))
verdicts = flatten(parallel([lambda b=b, k=k: check(b, sample=k) for b in batches(found, 6) for k in range(skeptics)]))
result = report(vote(found, verdicts, need=skeptics // 2 + 1))"""
RUNAWAY = 'for i in range(1000000):\n    agent("look again", label=f"again#{i}")\nresult = report([])'
estimates = {"fixed plan": dry_run(FIXED_PROGRAM)[0], "fit the budget, sees 150": dry_run(FIT, 150)[0], "fit the budget, sees 45": dry_run(FIT, 45)[0]}
for name, e in estimates.items():
    print(f"{name:<24} {e['agents']:>3} workers, {e['credits']:>4.1f} credits | gate at a budget of 45: {approve(e, 45)[0]}")
print("runaway passes the rules:", not check_program(RUNAWAY, names), "| dry run:", dry_run(RUNAWAY)[1][0])

#### OUTPUT ####
fixed plan                49 workers, 10.1 credits | gate at a budget of 45: approved
fit the budget, sees 150 118 workers, 23.9 credits | gate at a budget of 45: held
fit the budget, sees 45   40 workers,  8.3 credits | gate at a budget of 45: approved
runaway passes the rules: True | dry run: line 1: the dry run ended cancelled: 1000 workers refused by the agent limit
```

同じプログラムでも、リハーサルが見る予算が 150 なら 23.9 クレジット、45 なら 8.3 クレジットになる。

![](https://miro.medium.com/v2/resize:fit:6160/1*jFU3jVM56WbBwFUTJ4UZEA.png)（未取得）

有料の呼び出しの前にすべて見積もられた計画（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

したがって、リハーサルは実際のランと同じ予算を見なければならない。固定計画の見積もり 10.1 クレジットは、実際の 3 回のランの 13.8 より 27% 低かった。

## リードプランナー

リードのファクトシートは通常のコードが書く。シートは費用がかからず、ランごとに変わらない。以下は、その抜粋である。

```
#### OUTPUT ####
THE WORK
- 849 Python files, 91,327 lines, about 1,348,181 tokens with line numbers. The largest file is 13,353 tokens.

MEASURED SO FAR
- The measured best shard size is 100k tokens.

PRICES AND LIMITS
- Price per call in credits: worker 0.2, fast 0.2, judge 0.2, lead 0.5. Billing is per call, not per token.
- At most 1000 workers per run, and about 32 run at the same time.
- Budget for this job: 150 credits.
```

ファイル数とトークン数、測定したいくつかの比率、価格を含み、1,348,181 トークンの仕事に対して約 500 トークンである。

- `left out:` シートを作るコード（文字列の整形が約 20 行）

`Lead` はモデルと対話し、読んだ量の集計を保つ。

```
"""lead.py: the lead reads a fact sheet and writes the plan."""
import re

from bench import WORK
from config import MODELS, PRICE, PROMPTS, TEMPERATURE, TOP_P
from kit import AuditKit
from llm import LLM, Budget
from plans import approve, dry_run, run_program
from runtime import Run

FENCE = "`" * 3                                           # three backticks, built so this file's own fence stays open


class Lead:
    """The lead: it reads the fact sheet and writes plan programs."""
    def __init__(self, llm):
        self.llm, self.read = llm, []

    def ask(self, messages, sample=0):
        r = self.llm.chat(MODELS["lead"], messages, role="lead", sample=sample, temperature=TEMPERATURE, top_p=TOP_P, max_tokens=8000)
        self.read.append(r.prompt_tokens)                # kept, to count what the lead had to read
        return r
```

`write_program` は計画を求め、それを検査し、リハーサルを行い、見つかった問題をすべて返す。修正は最大 2 回までである。

```
# lead.py
    def write_program(self, job, page, budget=150, sample=0, repairs=2):
        # the job and the fact sheet are all the lead reads
        messages = [{"role": "system", "content": PROMPTS["lead"]}, {"role": "user", "content": f"THE JOB\n{job}\n\n{page}"}]
        attempts = []
        for _ in range(1 + repairs):
            r = self.ask(messages, sample)
            # take out the python block, then check and rehearse it
            m = re.search(FENCE + r"(?:python|py)?\s*\n(.*?)" + FENCE, r.text, re.S)
            src = m.group(1).strip() if m else None
            est, problems = dry_run(src, budget) if src else (None, [f"line 1: the reply has no {FENCE}python block"])
            attempts.append({"src": src, "problems": problems, "estimate": est})
            if not problems:
                break
            # hand every problem back in the checker's own words
            messages += [{"role": "assistant", "content": r.text[:8000]}, {"role": "user", "content": "Your program has these problems:\n- "
                         + "\n- ".join(problems[:8]) + f"\nSend the whole corrected program in one {FENCE}python block."}]
        return {"src": src, "valid": not problems, "tries": len(attempts), "attempts": attempts, "estimate": est}
```

私は同じリードに、サンプル番号ごとに 1 本ずつ、10 本のプログラムを書かせた。ここから先のモデルは実物であり、各出力は元のランが記録したものである。そのランでは、失敗した呼び出しの再試行と、各懐疑者へのサンドボックスの結果の提示も行ったが、この構築では省いている。

```
from pathlib import Path
from lead import Lead
from llm import http_client

JOB = "Find the behaviour bugs in a library of 849 Python files [...]. Report each bug with its file, its line and a call that shows it."
PAGE = Path("page.txt").read_text()                              # the fact sheet shown above
live = LLM(Ledger("ledger.sqlite"), client=http_client)          # the real model
programs = [Lead(live).write_program(JOB, PAGE, budget=150, sample=k) for k in range(10)]
print("tries  workers  credits")
for w in programs:
    print(f"{w['tries']:>5} {w['estimate']['agents']:>8} {w['estimate']['credits']:>8.1f}")

#### OUTPUT ####
tries  workers  credits
    1      263     52.9
    1      182     36.4
    1      261     52.5
    2      173     34.9
    2      252     50.4
    2      112     22.4
    2      196     39.2
    1      226     45.5
    1      263     52.9
    1      263     52.9
```

6 本は最初の試行で有効だった。修正が必要だった 4 本（`tries` が 2）は、すべて同じ規則、つまり長さの制限に違反しており、上限 80 行のところ、103 行、176 行、141 行、159 行だった。10 本すべてがループし、結果を見て判断したが、`budget()` を読んだのは 1 本だけだった。

![](https://miro.medium.com/v2/resize:fit:5961/1*XGYH0RYtWLHSyZAcHKUEQw.png)（未取得）

同じリードが書いた 10 本のプログラム（作成: @fareedkhandev）

## 実際のライブラリの完全な監査

`audit` は、リードの最初の草稿からバックグラウンドの実行まで、すべての段階を順に実行する。

```
# lead.py
def audit(llm, job, page, budget=150, sample=0, person=None):
    lead = Lead(llm)
    plan = lead.write_program(job, page, budget, sample)
    decision, why = approve(plan["estimate"], budget, person)
    if decision != "approved":
        return {"decision": decision, "why": why, "plan": plan}

    # the approved plan runs on a budget of its own
    run = Run("the lead's own plan", job, llm=LLM(llm.ledger, llm.mode, llm.client, llm.scripted, Budget(budget)), run_id=f"d{sample}", concurrency=32)
    result = run.start(lambda r: run_program(plan["src"], AuditKit(run, sample))).wait()

    # which files the scan workers saw
    seen = {p for t in run.threads if t.role == "scan" for p in re.findall(r"^### (\S+)$", t.messages[1]["content"], re.M)}
    stats = {"agents": len(run.threads), "calls": sum(len(t.replies) for t in run.threads), "covered": seen >= set(WORK),
             "credits": sum(PRICE.get(t.model, 0.2) * len(t.replies) for t in run.threads)}

    return {"decision": decision, "why": why, "plan": plan, "run": run, "result": result, "stats": stats, "lead_read": sum(lead.read)}
```

予算 150 クレジットのもとで、リードの最初のプログラムは、263 人のワーカーと 52.9 クレジットと見積もられ、自動の上限である 40 を超えていた。見積もりを見る前に書いた私の常設の規則により、予算の半分未満であることから承認された。そのプログラムの核心部分を切り詰めて以下に示す。

```
# the lead's own program, trimmed to its core
phase("Scan")
shardlist = list(shards(100000))
roundlenses = ["general", "logic", "boundaries", "state"] * 3 + ["general", "logic"]       # fourteen rounds

allfindings = []

for sampleid, lens in enumerate(roundlenses):
    found = flatten(parallel([lambda s=s, l=lens, r=sampleid: scan(s, l, sample=r) for s in shardlist]))
    allfindings.extend(found)

candidates = dedupe(allfindings)
phase("Verify")

verdicts = flatten(parallel([lambda b=b, k=k: check(b, sample=k) for b in batches(candidates, 8) for k in range(3)]))
confirmed = vote(candidates, verdicts, need=2)

phase("Report")
result = report(confirmed)
```

14 回のスキャンの周回、入れ替えるレンズ、バッチごとの 3 人の懐疑者は、予算の半分未満に収めるという指示に合わせてリードが自分で選んだものである。

```
from bench import match
from lead import audit

out = audit(live, JOB, PAGE, budget=150, sample=0, person=lambda est: est["credits"] <= 75)    # my standing rule: half the job budget
est, score = out["plan"]["estimate"], match(out["result"]["bugs"])
print(f"estimate {est['agents']} workers and {est['credits']:.1f} credits, gate: {out['decision']}")
print(f"{out['run'].status}: {out['stats']['agents']} workers, {out['stats']['calls']} calls, {out['stats']['credits']:.1f} credits at full price")
print(f"{len(out['result']['bugs'])} bugs reported, scored against the hidden key: recall {score['recall']:.2f}, precision {score['precision']:.2f} "
      f"({score['tp']} planted, {score['fp']} other places)")
print(f"the lead read {out['lead_read']:,} prompt tokens in all, and every file was read by a scan worker: {out['stats']['covered']}")

#### OUTPUT ####
estimate 263 workers and 52.9 credits, gate: approved
completed: 236 workers, 247 calls, 49.7 credits at full price
50 bugs reported, scored against the hidden key: recall 0.53, precision 0.76 (38 planted, 12 other places)
the lead read 1,780 prompt tokens in all, and every file was read by a scan worker: True
```

台帳は、すべての呼び出しの時間を測っていた。

![](https://miro.medium.com/v2/resize:fit:6409/1*TxDtdEhnvMNryosIaGpJ3w.png)（未取得）

台帳から見た 1 回のラン（作成: @fareedkhandev）

主要な有料セッションでは、呼び出しの合計 120 分に対して実時間は 41 分で、遅いフェーズは検証だった。193 回のスキャンの呼び出しは 14 分で済んだのに対し、39 回の懐疑者の呼び出しは 23 分かかった。

リードの 1 回の計画の呼び出しが読んだプロンプトは 1,780 トークンだった。エージェント 1 つだけでは、1 つのプロンプトで最大 91,171 トークンを抱え、スキャンのワーカーは合計で 1,840 万トークンを読んだ。

シートの予算が 150 でなく 20 または 60 クレジットのとき、リードの計画の費用は 8.3 と 18.1 で、バグの 28% と 39% を捕らえた。

## 5 つの設計の評価

1 つの採点器と 1 つの非公開キーで、5 つすべてを判定する。

- **A**: 1 つのエージェントが単独で動く。
- **A2**: 動的ランの予算を与えた、そのエージェント。
- **B**: ヘルパーを使うリード。
- **C**: 人が手で書いた、決まった手順の計画。
- **D**: 動的ワークフロー。

```
#### OUTPUT ####
  design  runs  mean recall  mean precision  mean credits
  ------  ----  -----------  --------------  ------------
  A          3         0.02            1.00          23.7
  A2         2         0.04            0.78          46.4
  B          1         0.17            0.67          10.3
  C          3         0.30            0.82          13.8
  D          3         0.45            0.71          48.4
```

区間は、ランのブートストラップによる再標本から求めた。

```
#### OUTPUT ####
[boot] mean recall D - A: 95% interval +0.30 to +0.56
[boot] mean recall D - A2: 95% interval +0.28 to +0.54
[boot] mean recall D - C: 95% interval +0.06 to +0.25
```

費用だけでは、この差を説明できない。248 ターンを与えられたエージェントでも、やはり自分で止まった。

![](https://miro.medium.com/v2/resize:fit:6027/1*VdOzlBWXoXymkFQHPzXMHA.png)（未取得）

設計ごとの各ランの再現率（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

リードの計画は、固定計画を +0.06 から +0.25 上回るが、費用は約 3.5 倍である。14 回スキャンするよう指示した固定計画は一度も実行していないので、この向上を、より多く読んだことと、より良く計画したことに分けることはできない。

![](https://miro.medium.com/v2/resize:fit:5950/1*2EZvQJvjfGPW78NtoWlaPw.png)（未取得）

埋め込まれた各バグが失われた場所（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

どちらのワークフローもすべてのファイルを読んだので、見逃されたバグの大半は、読まれたのに報告されなかったものである。H1 と H1b と H5 は成り立った。2 回目のスキャンの周回が加えたバグは、5 個、6 個、2 個である。

H4 は 2 つの基準をどちらも満たさなかった。懐疑者は適合率を 0.25 高めたが、区間の下端 +0.13 は +0.15 に届かず、再現率は最大 0.069 下がった可能性がある。H6 は成り立たなかった。懐疑者の得点は、失敗する呼び出しありで 0.84、なしで 0.85 だった。

## アブレーションの台帳

各機能について、それを取り除くと、その機能が改善するはずだった数値がどう変わるかを測った。

![](https://miro.medium.com/v2/resize:fit:5950/1*lLM_PgEXTBNYd070V0Dfxg.png)（未取得）

各機能を取り除いたときに失われるもの（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

2 回目のスキャンの周回と懐疑者による検証は、呼び出しの費用に見合った。一方、レンズ、サンドボックス、世代をまたぐ審判は、どちらとも言えない結果だった。あるランの 40 か所では、懐疑者 1 人の場合、再現率を落とさずに、3 人の場合より適合率が 0.08 高かった。ただし、区間は +0.003 から始まる。

## 分かっている限界

私の 11 個の予測のうち、成り立ったのは 3 個である。

![](https://miro.medium.com/v2/resize:fit:5957/1*5fI_IGb6inboGqK1LJXVBw.png)（未取得）

11 個の予測と、実際に起きたこと（作成: [Fareed Khan](https://medium.com/u/b856005e5ecd?source=post_page---user_mention--d304abd20dd0------------------------------------------)）

動的ランは、エージェント 1 つの場合より一貫していたわけではなかった。ランごとに計画が違ったためかもしれない。費用は固定計画の 3.5 倍で、適合率は 0.82 に対して 0.71 である。キーの外にある場所はすべて誤検知として数えるため、適合率は下限である。

各設計のラン数は 3 回以下で、1 つのライブラリと 1 つのモデルファミリーでの結果であり、区間は広い。ライブラリは公開されているが、その 72 個の関数をモデルに書き戻させたところ、元との類似度の中央値は 0.17 にとどまった。

## この研究の費用

3 日間でランは 2,616 回の呼び出しを行い、557.4 クレジットを使った。モデルの時間にして約 29 時間である。

これをもとに構築するなら、まず実際の 1 回のランで、ブラインドの代役を較正し、リードのループに停止の規則を与えるとよい。コード、データ、ノートブックの全体は、リポジトリにある。

[GitHub - FareedKhan-dev/dynamic-workflow-agents: Dynamic Workflows from… の Claude 版と Qwen 版 Dynamic Workflows from Scratch の Claude 版と Qwen 版 - FareedKhan-dev/dynamic-workflow-agents github.com](https://github.com/FareedKhan-dev/dynamic-workflow-agents?source=post_page-----d304abd20dd0------------------------------------------)
