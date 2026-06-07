use serde::Serialize;
use std::path::Path;
use std::process::Command;

#[derive(Serialize)]
pub struct CliRunResult {
    pub exit_code: i32,
    pub stdout: String,
    pub stderr: String,
}

/// Decode la sortie console : UTF-8 valide (Windscribe CLI) sinon OEM Windows (ipconfig, etc.).
fn decode_console_bytes(bytes: &[u8]) -> String {
    if bytes.is_empty() {
        return String::new();
    }

    if let Ok(text) = std::str::from_utf8(bytes) {
        return text.trim().to_string();
    }

    #[cfg(target_os = "windows")]
    {
        let cp850 = encoding_rs::Encoding::for_label(b"ibm850")
            .unwrap_or(encoding_rs::WINDOWS_1252);

        for encoding in [cp850, encoding_rs::WINDOWS_1252] {
            let (decoded, _, had_errors) = encoding.decode(bytes);

            if !had_errors {
                return decoded.into_owned().trim().to_string();
            }
        }

        let (decoded, _, _) = cp850.decode(bytes);
        return decoded.into_owned().trim().to_string();
    }

    String::from_utf8_lossy(bytes).trim().to_string()
}

fn run_command(program: &str, args: &[&str]) -> Result<CliRunResult, String> {
    let output = Command::new(program)
        .args(args)
        .output()
        .map_err(|error| format!("Impossible d'executer {program}: {error}"))?;

    Ok(CliRunResult {
        exit_code: output.status.code().unwrap_or(-1),
        stdout: decode_console_bytes(&output.stdout),
        stderr: decode_console_bytes(&output.stderr),
    })
}

/// Execute un programme dont le chemin est fourni par l'utilisateur (ex. windscribe-cli.exe).
#[tauri::command]
pub fn run_cli_program(program: String, args: Vec<String>) -> Result<CliRunResult, String> {
    let path = Path::new(program.trim());

    if !path.is_file() {
        return Err(format!("Executable introuvable : {}", path.display()));
    }

    let arg_refs: Vec<&str> = args.iter().map(String::as_str).collect();
    run_command(path.to_str().ok_or_else(|| "Chemin executable invalide".to_string())?, &arg_refs)
}

/// Ferme les processus Chrome / Chromium (Windows).
#[tauri::command]
pub fn close_chrome_processes() -> Result<CliRunResult, String> {
    #[cfg(target_os = "windows")]
    {
        let mut details: Vec<String> = Vec::new();

        for process_name in ["chrome.exe", "chromium.exe", "chromedriver.exe"] {
            match run_command("taskkill", &["/F", "/IM", process_name, "/T"]) {
                Ok(result) => {
                    if !result.stdout.is_empty() {
                        details.push(result.stdout);
                    } else if !result.stderr.is_empty() {
                        details.push(result.stderr);
                    }
                }
                Err(error) => details.push(error),
            }
        }

        return Ok(CliRunResult {
            exit_code: 0,
            stdout: details.join("\n"),
            stderr: String::new(),
        });
    }

    #[cfg(not(target_os = "windows"))]
    {
        Err("Fermeture Chrome automatique disponible uniquement sur Windows.".to_string())
    }
}

/// Vide le cache DNS Windows (ipconfig /flushdns).
#[tauri::command]
pub fn flush_dns_windows() -> Result<CliRunResult, String> {
    #[cfg(target_os = "windows")]
    {
        return run_command("ipconfig", &["/flushdns"]);
    }

    #[cfg(not(target_os = "windows"))]
    {
        Err("Flush DNS automatique disponible uniquement sur Windows.".to_string())
    }
}
