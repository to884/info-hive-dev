// ADR-0010 の PoC。独自スキーム wiki:// から静的 HTML を配り、駆動スクリプトの報告を集めて JSON に書く。配布対象ではない。
use std::borrow::Cow;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::http::{header, Response, StatusCode};
use tauri::{WebviewUrl, WebviewWindowBuilder};

const CSP: &str = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'";
const PROBE: &str = include_str!("../../static-test/probe.js");
const DRIVER: &str = include_str!("driver.js");

#[derive(Default)]
struct Collected {
    steps: Vec<serde_json::Value>,
    requests: Vec<String>,
    non_get: Vec<String>,
}

fn mime(p: &Path) -> &'static str {
    match p.extension().and_then(|e| e.to_str()).unwrap_or("").to_ascii_lowercase().as_str() {
        "html" => "text/html; charset=utf-8",
        "js" => "text/javascript; charset=utf-8",
        "css" => "text/css; charset=utf-8",
        "json" => "application/json; charset=utf-8",
        "svg" => "image/svg+xml",
        "png" => "image/png",
        "pdf" => "application/pdf",
        _ => "application/octet-stream",
    }
}

fn resp(status: StatusCode, ct: &str, body: Vec<u8>) -> Response<Cow<'static, [u8]>> {
    Response::builder()
        .status(status)
        .header(header::CONTENT_TYPE, ct)
        .header("Content-Security-Policy", CSP)
        .header("X-Content-Type-Options", "nosniff")
        .body(Cow::Owned(body))
        .unwrap()
}

fn write_result(c: &Collected, reason: &str, app: &tauri::AppHandle) {
    let out = std::env::var("BROWSE_RESULT").unwrap_or_else(|_| "tauri-result.json".into());
    let doc = serde_json::json!({
        "reason": reason,
        "os": std::env::consts::OS,
        "arch": std::env::consts::ARCH,
        "tauri": tauri::VERSION,
        "webview": tauri::webview_version().unwrap_or_else(|e| format!("unknown: {e}")),
        "steps": c.steps,
        "schemeRequests": c.requests,
        "nonGetRequests": c.non_get,
    });
    let _ = std::fs::write(&out, serde_json::to_string_pretty(&doc).unwrap().as_bytes());
    let h = app.clone();
    std::thread::spawn(move || {
        std::thread::sleep(Duration::from_millis(300));
        h.exit(0);
    });
}

fn main() {
    let root: PathBuf = PathBuf::from(std::env::var("BROWSE_ROOT").expect("BROWSE_ROOT")).canonicalize().expect("root");
    let state = Arc::new(Mutex::new(Collected::default()));
    let st = state.clone();
    let root2 = root.clone();

    tauri::Builder::default()
        .register_uri_scheme_protocol("wiki", move |ctx, request| {
            let uri = request.uri();
            let raw_path = uri.path().to_string();
            let mut c = st.lock().unwrap();
            if request.method() != tauri::http::Method::GET {
                c.non_get.push(format!("{} {}", request.method(), raw_path));
                return resp(StatusCode::METHOD_NOT_ALLOWED, "text/plain; charset=utf-8", b"GET only".to_vec());
            }
            if raw_path == "/__report" {
                let q = uri.query().unwrap_or("");
                let mut step = String::new();
                let mut data = String::new();
                for kv in q.split('&') {
                    if let Some((k, v)) = kv.split_once('=') {
                        let v = percent_encoding::percent_decode_str(v).decode_utf8_lossy().to_string();
                        if k == "step" {
                            step = v
                        } else if k == "data" {
                            data = v
                        }
                    }
                }
                let v: serde_json::Value = serde_json::from_str(&data).unwrap_or(serde_json::json!({"raw": data}));
                c.steps.push(serde_json::json!({"name": step, "data": v}));
                if step == "done" {
                    write_result(&c, "completed", ctx.app_handle());
                }
                return resp(StatusCode::NO_CONTENT, "text/plain", vec![]);
            }
            let decoded = match percent_encoding::percent_decode_str(&raw_path).decode_utf8() {
                Ok(s) => s.to_string(),
                Err(_) => return resp(StatusCode::BAD_REQUEST, "text/plain; charset=utf-8", b"bad utf-8".to_vec()),
            };
            c.requests.push(decoded.clone());
            let rel = decoded.trim_start_matches('/');
            let rel = if rel.is_empty() { "index.html" } else { rel };
            if rel.contains('\0') || rel.contains('\\') || rel.split('/').any(|s| s == "..") {
                return resp(StatusCode::FORBIDDEN, "text/plain; charset=utf-8", b"forbidden".to_vec());
            }
            let full = root2.join(rel);
            match full.canonicalize() {
                Ok(p) if p.starts_with(&root2) && p.is_file() => match std::fs::read(&p) {
                    Ok(b) => resp(StatusCode::OK, mime(&p), b),
                    Err(_) => resp(StatusCode::INTERNAL_SERVER_ERROR, "text/plain; charset=utf-8", b"read error".to_vec()),
                },
                _ => resp(StatusCode::NOT_FOUND, "text/plain; charset=utf-8", b"not found".to_vec()),
            }
        })
        .setup(move |app| {
            let script = format!("{PROBE}\n{DRIVER}");
            let url: tauri::Url = "wiki://localhost/index.html".parse().unwrap();
            WebviewWindowBuilder::new(app, "main", WebviewUrl::CustomProtocol(url))
                .title("browse-poc")
                .inner_size(1000.0, 800.0)
                .initialization_script(script)
                .build()?;
            let h = app.handle().clone();
            let s2 = state.clone();
            std::thread::spawn(move || {
                let secs: u64 = std::env::var("BROWSE_TIMEOUT").ok().and_then(|v| v.parse().ok()).unwrap_or(60);
                std::thread::sleep(Duration::from_secs(secs));
                let c = s2.lock().unwrap();
                write_result(&c, &format!("timeout after {secs}s; steps reported: {}", c.steps.len()), &h);
            });
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("tauri");
}
