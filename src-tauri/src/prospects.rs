use chrono::{DateTime, NaiveDate, NaiveDateTime, TimeZone};
use chrono_tz::Europe::Paris;
use parking_lot::RwLock;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use tauri::State;

/// Desserialise une valeur qui peut etre null, manquante ou typee differemment.
/// Si la conversion echoue, on retourne la valeur par defaut (None pour Option).
fn lax_string<'de, D: serde::Deserializer<'de>>(deserializer: D) -> Result<String, D::Error> {
    let value: Option<serde_json::Value> = Option::deserialize(deserializer)?;
    Ok(match value {
        Some(serde_json::Value::String(s)) => s,
        Some(serde_json::Value::Number(n)) => n.to_string(),
        _ => String::new(),
    })
}

fn lax_bool<'de, D: serde::Deserializer<'de>>(deserializer: D) -> Result<bool, D::Error> {
    let value: Option<serde_json::Value> = Option::deserialize(deserializer)?;
    Ok(match value {
        Some(serde_json::Value::Bool(b)) => b,
        Some(serde_json::Value::Number(n)) => n.as_i64().unwrap_or(0) != 0,
        Some(serde_json::Value::String(s)) => matches!(s.to_lowercase().as_str(), "true" | "1" | "yes"),
        _ => false,
    })
}

fn lax_i64<'de, D: serde::Deserializer<'de>>(deserializer: D) -> Result<i64, D::Error> {
    let value: Option<serde_json::Value> = Option::deserialize(deserializer)?;
    Ok(match value {
        Some(serde_json::Value::Number(n)) => n.as_i64().unwrap_or_else(|| n.as_f64().unwrap_or(0.0) as i64),
        Some(serde_json::Value::String(s)) => s.parse::<i64>().unwrap_or(0),
        Some(serde_json::Value::Bool(b)) => if b { 1 } else { 0 },
        _ => 0,
    })
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LinkedinProspect {
    #[serde(default, deserialize_with = "lax_i64")]
    pub id: i64,
    #[serde(default, deserialize_with = "lax_string")]
    pub first_name: String,
    #[serde(default, deserialize_with = "lax_string")]
    pub last_name: String,
    #[serde(default)]
    pub position: Option<String>,
    #[serde(default)]
    pub company: Option<String>,
    #[serde(default)]
    pub industry: Option<String>,
    #[serde(default)]
    pub city: Option<String>,
    #[serde(default)]
    pub region: Option<String>,
    #[serde(default)]
    pub linkedin_url: Option<String>,
    #[serde(default)]
    pub company_linkedin_url: Option<String>,
    #[serde(default)]
    pub website_url: Option<String>,
    #[serde(default)]
    pub email: Option<String>,
    #[serde(default)]
    pub phone: Option<String>,
    #[serde(default, deserialize_with = "lax_string")]
    pub status: String,
    #[serde(default, deserialize_with = "lax_bool")]
    pub is_favorite: bool,
    #[serde(default)]
    pub invitation_sent_at: Option<String>,
    #[serde(default)]
    pub invitation_accepted_at: Option<String>,
    #[serde(default)]
    pub message1_sent_at: Option<String>,
    #[serde(default)]
    pub replied_at: Option<String>,
    #[serde(default, deserialize_with = "lax_bool")]
    pub positive_reply: bool,
    #[serde(default, deserialize_with = "lax_i64")]
    pub relances_count: i64,
    #[serde(default)]
    pub next_action: Option<String>,
    #[serde(default)]
    pub next_action_at: Option<String>,
    #[serde(default)]
    pub discovery_call_at: Option<String>,
    #[serde(default)]
    pub sales_call_at: Option<String>,
    #[serde(default)]
    pub proposal_amount: Option<f64>,
    #[serde(default)]
    pub signed_amount: Option<f64>,
    #[serde(default)]
    pub added_at_week: Option<String>,
    #[serde(default, deserialize_with = "lax_string")]
    pub created_at: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LocalBusinessProspect {
    #[serde(default, deserialize_with = "lax_i64")]
    pub id: i64,
    #[serde(default, deserialize_with = "lax_string")]
    pub name: String,
    #[serde(default)]
    pub category: Option<String>,
    #[serde(default)]
    pub subcategory: Option<String>,
    #[serde(default)]
    pub osm_type: Option<String>,
    #[serde(default)]
    pub osm_id: Option<String>,
    #[serde(default)]
    pub address: Option<String>,
    #[serde(default)]
    pub city: Option<String>,
    #[serde(default)]
    pub postal_code: Option<String>,
    #[serde(default)]
    pub region: Option<String>,
    #[serde(default)]
    pub country: Option<String>,
    #[serde(default)]
    pub latitude: Option<f64>,
    #[serde(default)]
    pub longitude: Option<f64>,
    #[serde(default)]
    pub phone: Option<String>,
    #[serde(default)]
    pub email: Option<String>,
    #[serde(default)]
    pub email_source: Option<String>,
    #[serde(default)]
    pub website: Option<String>,
    #[serde(default)]
    pub pages_jaunes_url: Option<String>,
    #[serde(default, deserialize_with = "lax_bool")]
    pub has_website: bool,
    #[serde(default)]
    pub seo_score: Option<i64>,
    #[serde(default)]
    pub performance_score: Option<i64>,
    #[serde(default)]
    pub accessibility_score: Option<i64>,
    #[serde(default)]
    pub best_practices_score: Option<i64>,
    #[serde(default)]
    pub lighthouse_fetched_at: Option<String>,
    #[serde(default)]
    pub enriched_at: Option<String>,
    #[serde(default, deserialize_with = "lax_string")]
    pub status: String,
    #[serde(default, deserialize_with = "lax_bool")]
    pub is_favorite: bool,
    #[serde(default)]
    pub contact_channel: Option<String>,
    #[serde(default)]
    pub next_action: Option<String>,
    #[serde(default)]
    pub next_action_at: Option<String>,
    #[serde(default)]
    pub first_contact_at: Option<String>,
    #[serde(default, deserialize_with = "lax_i64")]
    pub relances_count: i64,
    #[serde(default)]
    pub replied_at: Option<String>,
    #[serde(default, deserialize_with = "lax_bool")]
    pub positive_reply: bool,
    #[serde(default)]
    pub discovery_call_at: Option<String>,
    #[serde(default)]
    pub sales_call_at: Option<String>,
    #[serde(default)]
    pub proposal_amount: Option<f64>,
    #[serde(default)]
    pub signed_amount: Option<f64>,
    #[serde(default)]
    pub added_at_week: Option<String>,
    #[serde(default, deserialize_with = "lax_string")]
    pub created_at: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PaginationMeta {
    pub total: i64,
    pub per_page: i64,
    pub current_page: i64,
    pub last_page: i64,
    pub first_page: i64,
}

#[derive(Debug, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct LinkedinFilters {
    #[serde(default)]
    pub search: Option<String>,
    #[serde(default)]
    pub statuses: Option<Vec<String>>,
    #[serde(default)]
    pub is_favorite: Option<bool>,
    #[serde(default)]
    pub week: Option<String>,
    #[serde(default)]
    pub sort_by: Option<String>,
    #[serde(default)]
    pub sort_dir: Option<String>,
    #[serde(default)]
    pub page: Option<i64>,
    #[serde(default)]
    pub per_page: Option<i64>,
}

#[derive(Debug, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct LocalBusinessFilters {
    #[serde(default)]
    pub search: Option<String>,
    #[serde(default)]
    pub statuses: Option<Vec<String>>,
    #[serde(default)]
    pub category: Option<String>,
    #[serde(default)]
    pub city: Option<String>,
    #[serde(default)]
    pub region: Option<String>,
    #[serde(default)]
    pub postal_code: Option<String>,
    #[serde(default)]
    pub has_website: Option<bool>,
    #[serde(default)]
    pub has_email: Option<bool>,
    #[serde(default)]
    pub has_phone: Option<bool>,
    #[serde(default)]
    pub seo_score_max: Option<i64>,
    #[serde(default)]
    pub is_favorite: Option<bool>,
    #[serde(default)]
    pub week: Option<String>,
    #[serde(default)]
    pub sort_by: Option<String>,
    #[serde(default)]
    pub sort_dir: Option<String>,
    #[serde(default)]
    pub page: Option<i64>,
    #[serde(default)]
    pub per_page: Option<i64>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LinkedinQueryResult {
    pub data: Vec<LinkedinProspect>,
    pub meta: PaginationMeta,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LocalBusinessQueryResult {
    pub data: Vec<LocalBusinessProspect>,
    pub meta: PaginationMeta,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LinkedinCallEvent {
    pub prospect: LinkedinProspect,
    pub call_type: String,
    pub date_iso: String,
    pub has_time: bool,
    pub time_label: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LocalBusinessCallEvent {
    pub prospect: LocalBusinessProspect,
    pub call_type: String,
    pub date_iso: String,
    pub has_time: bool,
    pub time_label: String,
}

pub struct LinkedinStore(pub RwLock<Vec<LinkedinProspect>>);
pub struct LocalBusinessStore(pub RwLock<Vec<LocalBusinessProspect>>);

fn parse_iso_to_paris_date(iso: &str) -> Option<NaiveDate> {
    if let Ok(dt) = DateTime::parse_from_rfc3339(iso) {
        return Some(dt.with_timezone(&Paris).date_naive());
    }
    if let Ok(date) = NaiveDate::parse_from_str(iso, "%Y-%m-%d") {
        return Some(date);
    }
    if let Ok(ndt) = NaiveDateTime::parse_from_str(iso, "%Y-%m-%dT%H:%M:%S") {
        return Paris.from_local_datetime(&ndt).single().map(|dt| dt.date_naive());
    }
    if let Ok(ndt) = NaiveDateTime::parse_from_str(iso, "%Y-%m-%d %H:%M:%S") {
        return Paris.from_local_datetime(&ndt).single().map(|dt| dt.date_naive());
    }
    if iso.len() >= 10 {
        if let Ok(date) = NaiveDate::parse_from_str(&iso[..10], "%Y-%m-%d") {
            return Some(date);
        }
    }
    None
}

fn format_time_paris(iso: &str) -> String {
    if let Ok(dt) = DateTime::parse_from_rfc3339(iso) {
        return dt.with_timezone(&Paris).format("%H:%M").to_string();
    }
    if let Ok(ndt) = NaiveDateTime::parse_from_str(iso, "%Y-%m-%dT%H:%M:%S") {
        if let Some(dt) = Paris.from_local_datetime(&ndt).single() {
            return dt.format("%H:%M").to_string();
        }
    }
    String::new()
}

fn parse_iso_ms(iso: &str) -> Option<i64> {
    if let Ok(dt) = DateTime::parse_from_rfc3339(iso) {
        return Some(dt.timestamp_millis());
    }
    if let Ok(ndt) = NaiveDateTime::parse_from_str(iso, "%Y-%m-%dT%H:%M:%S") {
        return Paris.from_local_datetime(&ndt).single().map(|dt| dt.timestamp_millis());
    }
    if let Ok(ndt) = NaiveDateTime::parse_from_str(iso, "%Y-%m-%d %H:%M:%S") {
        return Paris.from_local_datetime(&ndt).single().map(|dt| dt.timestamp_millis());
    }
    if let Ok(date) = NaiveDate::parse_from_str(iso, "%Y-%m-%d") {
        return Paris
            .from_local_datetime(&date.and_hms_opt(0, 0, 0)?)
            .single()
            .map(|dt| dt.timestamp_millis());
    }
    None
}

fn lowercase_contains(haystack: &str, needle_lc: &str) -> bool {
    haystack.to_lowercase().contains(needle_lc)
}

fn slice_with_meta<T: Clone>(items: Vec<T>, page: i64, per_page: i64) -> (Vec<T>, PaginationMeta) {
    let total: i64 = items.len() as i64;
    let per_page: i64 = if per_page <= 0 { 50 } else { per_page };
    let page: i64 = if page <= 0 { 1 } else { page };
    let last_page: i64 = if total == 0 {
        1
    } else {
        ((total as f64) / (per_page as f64)).ceil() as i64
    };

    let start: usize = ((page - 1).max(0) as usize) * per_page as usize;
    let end: usize = (page as usize * per_page as usize).min(items.len());
    let data: Vec<T> = if start < items.len() { items[start..end].to_vec() } else { Vec::new() };

    let meta: PaginationMeta = PaginationMeta {
        total,
        per_page,
        current_page: page,
        last_page,
        first_page: 1,
    };
    (data, meta)
}

#[tauri::command]
pub fn linkedin_set_all(prospects: Vec<LinkedinProspect>, store: State<'_, LinkedinStore>) {
    let mut guard = store.0.write();
    *guard = prospects;
}

#[tauri::command]
pub fn linkedin_upsert(prospect: LinkedinProspect, store: State<'_, LinkedinStore>) {
    let mut guard = store.0.write();
    if let Some(pos) = guard.iter().position(|p| p.id == prospect.id) {
        guard[pos] = prospect;
    } else {
        guard.insert(0, prospect);
    }
}

#[tauri::command]
pub fn linkedin_upsert_many(prospects: Vec<LinkedinProspect>, store: State<'_, LinkedinStore>) {
    let mut guard = store.0.write();
    for prospect in prospects {
        if let Some(pos) = guard.iter().position(|p| p.id == prospect.id) {
            guard[pos] = prospect;
        } else {
            guard.push(prospect);
        }
    }
}

#[tauri::command]
pub fn linkedin_remove(id: i64, store: State<'_, LinkedinStore>) {
    let mut guard = store.0.write();
    guard.retain(|p| p.id != id);
}

#[tauri::command]
pub fn linkedin_clear(store: State<'_, LinkedinStore>) {
    let mut guard = store.0.write();
    guard.clear();
}

#[tauri::command]
pub fn linkedin_count(store: State<'_, LinkedinStore>) -> i64 {
    let guard = store.0.read();
    guard.len() as i64
}

#[tauri::command]
pub fn linkedin_query(
    filters: LinkedinFilters,
    store: State<'_, LinkedinStore>,
) -> LinkedinQueryResult {
    let guard = store.0.read();
    let search_lc: Option<String> = filters.search.as_ref().map(|s| s.to_lowercase());
    let statuses: Option<&Vec<String>> = filters.statuses.as_ref();
    let week: Option<&String> = filters.week.as_ref();
    let only_favorite: bool = matches!(filters.is_favorite, Some(true));

    let mut filtered: Vec<LinkedinProspect> = guard
        .par_iter()
        .filter(|p| {
            if let Some(ref s) = search_lc {
                let hits: bool = lowercase_contains(&p.first_name, s)
                    || lowercase_contains(&p.last_name, s)
                    || p.position.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false)
                    || p.company.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false)
                    || p.city.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false)
                    || p.industry.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false);
                if !hits {
                    return false;
                }
            }
            if let Some(st) = statuses {
                if !st.iter().any(|s| s == &p.status) {
                    return false;
                }
            }
            if only_favorite && !p.is_favorite {
                return false;
            }
            if let Some(w) = week {
                if p.added_at_week.as_deref() != Some(w.as_str()) {
                    return false;
                }
            }
            true
        })
        .cloned()
        .collect();

    let sort_by: &str = filters.sort_by.as_deref().unwrap_or("createdAt");
    let desc: bool = filters.sort_dir.as_deref().unwrap_or("desc") == "desc";

    filtered.par_sort_by(|a, b| {
        let ord = match sort_by {
            "lastName" => a.last_name.cmp(&b.last_name),
            "nextActionAt" => a.next_action_at.cmp(&b.next_action_at),
            "invitationSentAt" => a.invitation_sent_at.cmp(&b.invitation_sent_at),
            _ => a.created_at.cmp(&b.created_at),
        };
        if desc { ord.reverse() } else { ord }
    });

    let (data, meta) = slice_with_meta(
        filtered,
        filters.page.unwrap_or(1),
        filters.per_page.unwrap_or(50),
    );
    LinkedinQueryResult { data, meta }
}

#[tauri::command]
pub fn linkedin_calls_by_day(
    date_iso: String,
    store: State<'_, LinkedinStore>,
) -> Vec<LinkedinCallEvent> {
    let target: NaiveDate = match NaiveDate::parse_from_str(&date_iso, "%Y-%m-%d") {
        Ok(d) => d,
        Err(_) => return Vec::new(),
    };
    let guard = store.0.read();
    let mut events: Vec<LinkedinCallEvent> = guard
        .par_iter()
        .flat_map_iter(|p| {
            let mut out: Vec<LinkedinCallEvent> = Vec::new();
            if let Some(iso) = p.discovery_call_at.as_deref() {
                if parse_iso_to_paris_date(iso) == Some(target) {
                    let has_time: bool = iso.len() > 10;
                    out.push(LinkedinCallEvent {
                        prospect: p.clone(),
                        call_type: "discovery".into(),
                        date_iso: iso.to_string(),
                        has_time,
                        time_label: if has_time { format_time_paris(iso) } else { String::new() },
                    });
                }
            }
            if let Some(iso) = p.sales_call_at.as_deref() {
                if parse_iso_to_paris_date(iso) == Some(target) {
                    let has_time: bool = iso.len() > 10;
                    out.push(LinkedinCallEvent {
                        prospect: p.clone(),
                        call_type: "sales".into(),
                        date_iso: iso.to_string(),
                        has_time,
                        time_label: if has_time { format_time_paris(iso) } else { String::new() },
                    });
                }
            }
            out
        })
        .collect();

    events.sort_by(|a, b| {
        let am: i64 = parse_iso_ms(&a.date_iso).unwrap_or(i64::MAX);
        let bm: i64 = parse_iso_ms(&b.date_iso).unwrap_or(i64::MAX);
        am.cmp(&bm)
    });
    events
}

#[tauri::command]
pub fn linkedin_tasks_due(
    horizon_days: i64,
    now_iso: String,
    store: State<'_, LinkedinStore>,
) -> Vec<LinkedinProspect> {
    let now_ms: i64 = match parse_iso_ms(&now_iso) {
        Some(v) => v,
        None => return Vec::new(),
    };
    let horizon_ms: i64 = now_ms + horizon_days * 86_400_000;
    let guard = store.0.read();
    let mut out: Vec<LinkedinProspect> = guard
        .par_iter()
        .filter(|p| {
            if let Some(iso) = p.next_action_at.as_deref() {
                if let Some(ms) = parse_iso_ms(iso) {
                    return ms <= horizon_ms;
                }
            }
            false
        })
        .cloned()
        .collect();

    out.par_sort_by(|a, b| {
        let am: i64 = a.next_action_at.as_deref().and_then(parse_iso_ms).unwrap_or(i64::MAX);
        let bm: i64 = b.next_action_at.as_deref().and_then(parse_iso_ms).unwrap_or(i64::MAX);
        am.cmp(&bm)
    });
    out
}

#[tauri::command]
pub fn local_business_set_all(
    prospects: Vec<LocalBusinessProspect>,
    store: State<'_, LocalBusinessStore>,
) {
    let mut guard = store.0.write();
    *guard = prospects;
}

#[tauri::command]
pub fn local_business_upsert(
    prospect: LocalBusinessProspect,
    store: State<'_, LocalBusinessStore>,
) {
    let mut guard = store.0.write();
    if let Some(pos) = guard.iter().position(|p| p.id == prospect.id) {
        guard[pos] = prospect;
    } else {
        guard.insert(0, prospect);
    }
}

#[tauri::command]
pub fn local_business_upsert_many(
    prospects: Vec<LocalBusinessProspect>,
    store: State<'_, LocalBusinessStore>,
) {
    let mut guard = store.0.write();
    for prospect in prospects {
        if let Some(pos) = guard.iter().position(|p| p.id == prospect.id) {
            guard[pos] = prospect;
        } else {
            guard.push(prospect);
        }
    }
}

#[tauri::command]
pub fn local_business_remove(id: i64, store: State<'_, LocalBusinessStore>) {
    let mut guard = store.0.write();
    guard.retain(|p| p.id != id);
}

#[tauri::command]
pub fn local_business_clear(store: State<'_, LocalBusinessStore>) {
    let mut guard = store.0.write();
    guard.clear();
}

#[tauri::command]
pub fn local_business_count(store: State<'_, LocalBusinessStore>) -> i64 {
    let guard = store.0.read();
    guard.len() as i64
}

#[tauri::command]
pub fn local_business_query(
    filters: LocalBusinessFilters,
    store: State<'_, LocalBusinessStore>,
) -> LocalBusinessQueryResult {
    let guard = store.0.read();
    let search_lc: Option<String> = filters.search.as_ref().map(|s| s.to_lowercase());
    let statuses: Option<&Vec<String>> = filters.statuses.as_ref();
    let category_lc: Option<String> = filters.category.as_ref().map(|s| s.to_lowercase());
    let city_lc: Option<String> = filters.city.as_ref().map(|s| s.to_lowercase());
    let region_lc: Option<String> = filters.region.as_ref().map(|s| s.to_lowercase());
    let postal_code_lc: Option<String> = filters.postal_code.as_ref().map(|s| s.to_lowercase());
    let week: Option<&String> = filters.week.as_ref();
    let only_favorite: bool = matches!(filters.is_favorite, Some(true));

    let mut filtered: Vec<LocalBusinessProspect> = guard
        .par_iter()
        .filter(|p| {
            if let Some(ref s) = search_lc {
                let hits: bool = lowercase_contains(&p.name, s)
                    || p.subcategory.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false)
                    || p.category.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false)
                    || p.city.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false)
                    || p.email.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false)
                    || p.phone.as_deref().map(|v| lowercase_contains(v, s)).unwrap_or(false);
                if !hits {
                    return false;
                }
            }
            if let Some(st) = statuses {
                if !st.iter().any(|s| s == &p.status) {
                    return false;
                }
            }
            if let Some(ref c) = category_lc {
                if !p.category.as_deref().map(|v| lowercase_contains(v, c)).unwrap_or(false) {
                    return false;
                }
            }
            if let Some(ref c) = city_lc {
                if !p.city.as_deref().map(|v| lowercase_contains(v, c)).unwrap_or(false) {
                    return false;
                }
            }
            if let Some(ref r) = region_lc {
                if !p.region.as_deref().map(|v| lowercase_contains(v, r)).unwrap_or(false) {
                    return false;
                }
            }
            if let Some(ref pc) = postal_code_lc {
                if !p.postal_code.as_deref().map(|v| lowercase_contains(v, pc)).unwrap_or(false) {
                    return false;
                }
            }
            if let Some(has_website) = filters.has_website {
                if has_website != p.has_website {
                    return false;
                }
            }
            if let Some(has_email) = filters.has_email {
                let actually: bool = p.email.as_deref().map(|v| !v.is_empty()).unwrap_or(false);
                if has_email != actually {
                    return false;
                }
            }
            if let Some(has_phone) = filters.has_phone {
                let actually: bool = p.phone.as_deref().map(|v| !v.is_empty()).unwrap_or(false);
                if has_phone != actually {
                    return false;
                }
            }
            if let Some(max) = filters.seo_score_max {
                let score: i64 = p.seo_score.unwrap_or(i64::MAX);
                if score > max {
                    return false;
                }
            }
            if only_favorite && !p.is_favorite {
                return false;
            }
            if let Some(w) = week {
                if p.added_at_week.as_deref() != Some(w.as_str()) {
                    return false;
                }
            }
            true
        })
        .cloned()
        .collect();

    let sort_by: &str = filters.sort_by.as_deref().unwrap_or("createdAt");
    let desc: bool = filters.sort_dir.as_deref().unwrap_or("desc") == "desc";

    filtered.par_sort_by(|a, b| {
        let ord = match sort_by {
            "name" => a.name.cmp(&b.name),
            "nextActionAt" => a.next_action_at.cmp(&b.next_action_at),
            "seoScore" => a.seo_score.cmp(&b.seo_score),
            "performanceScore" => a.performance_score.cmp(&b.performance_score),
            _ => a.created_at.cmp(&b.created_at),
        };
        if desc { ord.reverse() } else { ord }
    });

    let (data, meta) = slice_with_meta(
        filtered,
        filters.page.unwrap_or(1),
        filters.per_page.unwrap_or(50),
    );
    LocalBusinessQueryResult { data, meta }
}

#[tauri::command]
pub fn local_business_calls_by_day(
    date_iso: String,
    store: State<'_, LocalBusinessStore>,
) -> Vec<LocalBusinessCallEvent> {
    let target: NaiveDate = match NaiveDate::parse_from_str(&date_iso, "%Y-%m-%d") {
        Ok(d) => d,
        Err(_) => return Vec::new(),
    };
    let guard = store.0.read();
    let mut events: Vec<LocalBusinessCallEvent> = guard
        .par_iter()
        .flat_map_iter(|p| {
            let mut out: Vec<LocalBusinessCallEvent> = Vec::new();
            if let Some(iso) = p.discovery_call_at.as_deref() {
                if parse_iso_to_paris_date(iso) == Some(target) {
                    let has_time: bool = iso.len() > 10;
                    out.push(LocalBusinessCallEvent {
                        prospect: p.clone(),
                        call_type: "discovery".into(),
                        date_iso: iso.to_string(),
                        has_time,
                        time_label: if has_time { format_time_paris(iso) } else { String::new() },
                    });
                }
            }
            if let Some(iso) = p.sales_call_at.as_deref() {
                if parse_iso_to_paris_date(iso) == Some(target) {
                    let has_time: bool = iso.len() > 10;
                    out.push(LocalBusinessCallEvent {
                        prospect: p.clone(),
                        call_type: "sales".into(),
                        date_iso: iso.to_string(),
                        has_time,
                        time_label: if has_time { format_time_paris(iso) } else { String::new() },
                    });
                }
            }
            out
        })
        .collect();

    events.sort_by(|a, b| {
        let am: i64 = parse_iso_ms(&a.date_iso).unwrap_or(i64::MAX);
        let bm: i64 = parse_iso_ms(&b.date_iso).unwrap_or(i64::MAX);
        am.cmp(&bm)
    });
    events
}

#[tauri::command]
pub fn local_business_tasks_due(
    horizon_days: i64,
    now_iso: String,
    store: State<'_, LocalBusinessStore>,
) -> Vec<LocalBusinessProspect> {
    let now_ms: i64 = match parse_iso_ms(&now_iso) {
        Some(v) => v,
        None => return Vec::new(),
    };
    let horizon_ms: i64 = now_ms + horizon_days * 86_400_000;
    let guard = store.0.read();
    let mut out: Vec<LocalBusinessProspect> = guard
        .par_iter()
        .filter(|p| {
            if let Some(iso) = p.next_action_at.as_deref() {
                if let Some(ms) = parse_iso_ms(iso) {
                    return ms <= horizon_ms;
                }
            }
            false
        })
        .cloned()
        .collect();

    out.par_sort_by(|a, b| {
        let am: i64 = a.next_action_at.as_deref().and_then(parse_iso_ms).unwrap_or(i64::MAX);
        let bm: i64 = b.next_action_at.as_deref().and_then(parse_iso_ms).unwrap_or(i64::MAX);
        am.cmp(&bm)
    });
    out
}
