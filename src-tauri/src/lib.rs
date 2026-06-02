mod prospects;

use parking_lot::RwLock;
use prospects::{LinkedinStore, LocalBusinessStore};
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_opener::init())
        .manage(LinkedinStore(RwLock::new(Vec::new())))
        .manage(LocalBusinessStore(RwLock::new(Vec::new())))
        .setup(|app| {
            // Ouvre automatiquement les DevTools en mode debug (tauri dev).
            // Sans effet sur les builds de production (tauri build sans --debug).
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            prospects::linkedin_set_all,
            prospects::linkedin_upsert,
            prospects::linkedin_upsert_many,
            prospects::linkedin_remove,
            prospects::linkedin_clear,
            prospects::linkedin_count,
            prospects::linkedin_query,
            prospects::linkedin_calls_by_day,
            prospects::linkedin_tasks_due,
            prospects::local_business_set_all,
            prospects::local_business_upsert,
            prospects::local_business_upsert_many,
            prospects::local_business_remove,
            prospects::local_business_clear,
            prospects::local_business_count,
            prospects::local_business_query,
            prospects::local_business_calls_by_day,
            prospects::local_business_tasks_due,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
