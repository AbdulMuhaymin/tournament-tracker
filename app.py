import json
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="BDSA Fall Football Fest 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_FILE = Path("data/tournament.json")
CSS_FILE = Path("styles.css")
ADMIN_PASSWORD = "Khullja Sim Sim"  # Change this password as needed


def load_css():
    if CSS_FILE.exists():
        st.markdown(f"<style>{CSS_FILE.read_text()}</style>", unsafe_allow_html=True)


def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def calculate_standings(data):
    stats = {}
    for t in data["teams"]:
        stats[t["name"]] = {
            "badge": t.get("badge", "⚽"),
            "MP": 0, "W": 0, "D": 0, "L": 0,
            "GF": 0, "GA": 0, "GD": 0, "Pts": 0,
            "form": []
        }

    for m in data["matches"]:
        if m["stage"] != "Round Robin" or m["status"] not in ("FT", "LIVE"):
            continue
        if m["score1"] is None or m["score2"] is None:
            continue

        t1, t2 = m["team1"], m["team2"]
        s1, s2 = int(m["score1"]), int(m["score2"])
        if t1 not in stats or t2 not in stats:
            continue

        stats[t1]["MP"] += 1
        stats[t2]["MP"] += 1
        stats[t1]["GF"] += s1
        stats[t1]["GA"] += s2
        stats[t2]["GF"] += s2
        stats[t2]["GA"] += s1

        if s1 > s2:
            stats[t1]["W"] += 1
            stats[t1]["Pts"] += 3
            stats[t1]["form"].append("W")
            stats[t2]["L"] += 1
            stats[t2]["form"].append("L")
        elif s2 > s1:
            stats[t2]["W"] += 1
            stats[t2]["Pts"] += 3
            stats[t2]["form"].append("W")
            stats[t1]["L"] += 1
            stats[t1]["form"].append("L")
        else:
            stats[t1]["D"] += 1
            stats[t2]["D"] += 1
            stats[t1]["Pts"] += 1
            stats[t2]["Pts"] += 1
            stats[t1]["form"].append("D")
            stats[t2]["form"].append("D")

    standings = []
    for name, st_val in stats.items():
        st_val["name"] = name
        st_val["GD"] = st_val["GF"] - st_val["GA"]
        standings.append(st_val)

    standings.sort(key=lambda x: (x["Pts"], x["GD"], x["GF"]), reverse=True)
    return standings


def calculate_player_stats(data):
    goals, yellows, reds = {}, {}, {}
    team_badges = {t["name"]: t.get("badge", "⚽") for t in data["teams"]}

    for m in data["matches"]:
        for ev in m.get("events", []):
            etype = ev.get("type")
            player = ev.get("player")
            team = ev.get("team")
            key = (player, team, team_badges.get(team, "⚽"))

            if etype == "goal":
                goals[key] = goals.get(key, 0) + 1
            elif etype == "yellow":
                yellows[key] = yellows.get(key, 0) + 1
            elif etype == "red":
                reds[key] = reds.get(key, 0) + 1

    sort_fn = lambda d: sorted(d.items(), key=lambda x: x[1], reverse=True)
    return sort_fn(goals), sort_fn(yellows), sort_fn(reds)


def render_match_card(m, team_badges):
    t1, t2 = m["team1"], m["team2"]
    b1, b2 = team_badges.get(t1, "🏳️"), team_badges.get(t2, "🏳️")
    s1 = m["score1"] if m["score1"] is not None else "-"
    s2 = m["score2"] if m["score2"] is not None else "-"

    w1 = "team-winner" if (m["status"] == "FT" and s1 != "-" and s1 > s2) else ""
    w2 = "team-winner" if (m["status"] == "FT" and s2 != "-" and s2 > s1) else ""
    arrow1 = " ◀" if w1 else ""
    arrow2 = " ◀" if w2 else ""

    # Count cards per team in this match
    y1 = sum(1 for e in m.get("events", []) if e["team"] == t1 and e["type"] == "yellow")
    r1 = sum(1 for e in m.get("events", []) if e["team"] == t1 and e["type"] == "red")
    y2 = sum(1 for e in m.get("events", []) if e["team"] == t2 and e["type"] == "yellow")
    r2 = sum(1 for e in m.get("events", []) if e["team"] == t2 and e["type"] == "red")

    cards1 = ("<span class='card-yellow'></span>" * y1) + ("<span class='card-red'></span>" * r1)
    cards2 = ("<span class='card-yellow'></span>" * y2) + ("<span class='card-red'></span>" * r2)

    status_cls = "status-live" if m["status"] == "LIVE" else ("status-ft" if m["status"] == "FT" else "")
    status_label = m["status"] if m["status"] in ("FT", "LIVE") else f"{m.get('date', '')} · {m.get('time', '')}"

    ev_list = []
    for e in m.get("events", []):
        if e["type"] == "goal":
            ev_list.append(f"⚽ {e['player']} ({e['team']})")
        elif e["type"] == "own_goal":
            ev_list.append(f"⚽ {e['player']} [OG]")
        elif e["type"] == "yellow":
            ev_list.append(f"🟨 {e['player']}")
        elif e["type"] == "red":
            ev_list.append(f"🟥 {e['player']}")

    ev_html = f"<div class='match-events'>{' · '.join(ev_list)}</div>" if ev_list else ""

    html = (
        f"<div class='match-box'>"
        f"<div class='match-meta'><span>{m['stage']} · Day {m['matchday']}</span>"
        f"<span class='{status_cls}'>{status_label}</span></div>"
        f"<div class='team-row {w1}'><span>{b1} {t1}{cards1}</span><span>{s1}{arrow1}</span></div>"
        f"<div class='team-row {w2}'><span>{b2} {t2}{cards2}</span><span>{s2}{arrow2}</span></div>"
        f"{ev_html}</div>"
    )
    return html


def render_standings_html(standings, full=True):
    headers = "<th>MP</th><th>W</th><th>D</th><th>L</th>"
    if full:
        headers += "<th>GF</th><th>GA</th>"
    headers += "<th>GD</th><th>Pts</th>"
    if full:
        headers += "<th>Form</th>"

    rows = ""
    for idx, s in enumerate(standings, start=1):
        q_cls = "qualify-bar" if idx <= 2 else ""
        form_html = ""
        if full:
            badges = []
            for f in s["form"][-5:]:
                symbol = "✓" if f == "W" else ("–" if f == "D" else "✕")
                badges.append(f"<span class='form-badge form-{f.lower()}'>{symbol}</span>")
            form_html = f"<td>{''.join(badges) if badges else '-'}</td>"

        gf_ga = f"<td>{s['GF']}</td><td>{s['GA']}</td>" if full else ""
        rows += (
            f"<tr>"
            f"<td class='left {q_cls}' style='padding-left:8px;'>{idx} &nbsp; {s['badge']} <b>{s['name']}</b></td>"
            f"<td>{s['MP']}</td><td>{s['W']}</td><td>{s['D']}</td><td>{s['L']}</td>"
            f"{gf_ga}<td>{s['GD']}</td><td><b>{s['Pts']}</b></td>{form_html}"
            f"</tr>"
        )

    return (
        f"<div class='g-card'>"
        f"<div class='g-card-title'>Standings</div>"
        f"<div class='g-card-subtitle'>Top 2 advance to the Final</div>"
        f"<table class='g-table'><thead><tr><th class='left'>Club</th>{headers}</tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )


# --- MAIN APP ---
load_css()
data = load_data()
standings = calculate_standings(data)
team_badges = {t["name"]: t.get("badge", "⚽") for t in data["teams"]}

# Sidebar Mode Switch
st.sidebar.title("⚙️ Navigation")
mode = st.sidebar.radio("View Mode", ["Public Tracker", "Admin Panel"])

t_info = data.get("tournament", {})
st.markdown(f"## 🏆 {t_info.get('name', 'Football Tournament')}")
st.caption(f"📍 {t_info.get('venue', '')}  |  ⏱️ {t_info.get('format', '')}")

if mode == "Public Tracker":
    tab_ov, tab_st, tab_stats, tab_squads = st.tabs(["Matches", "Standings", "Stats", "Squads"])

    with tab_ov:
        st.markdown("<div class='g-card-title'>Matches</div>", unsafe_allow_html=True)
        matches = data["matches"]
        for i in range(0, len(matches), 2):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(render_match_card(matches[i], team_badges), unsafe_allow_html=True)
            if i + 1 < len(matches):
                with c2:
                    st.markdown(render_match_card(matches[i + 1], team_badges), unsafe_allow_html=True)

    with tab_st:
        st.markdown(render_standings_html(standings, full=True), unsafe_allow_html=True)

    with tab_stats:
        goals, yellows, reds = calculate_player_stats(data)
        c_g, c_y, c_r = st.columns(3)

        def render_stat_box(title, items, label):
            if not items:
                return f"<div class='g-card'><div class='g-card-title'>{title}</div><p style='color:#70757a;font-size:13px;'>No records yet.</p></div>"
            rows = ""
            for idx, ((player, team, badge), count) in enumerate(items, 1):
                rows += f"<tr><td class='left'>{idx}. <b>{player}</b><br><span style='font-size:11px;color:#70757a;'>{badge} {team}</span></td><td><b>{count}</b></td></tr>"
            return f"<div class='g-card'><div class='g-card-title'>{title}</div><table class='g-table'><thead><tr><th class='left'>Player</th><th>{label}</th></tr></thead><tbody>{rows}</tbody></table></div>"

        with c_g:
            st.markdown(render_stat_box("⚽ Top Scorers", goals, "Goals"), unsafe_allow_html=True)
        with c_y:
            st.markdown(render_stat_box("🟨 Yellow Cards", yellows, "Cards"), unsafe_allow_html=True)
        with c_r:
            st.markdown(render_stat_box("🟥 Red Cards", reds, "Cards"), unsafe_allow_html=True)

    with tab_squads:
        cols = st.columns(2)
        for idx, team in enumerate(data["teams"]):
            with cols[idx % 2]:
                rows = "".join(
                    f"<tr><td class='left'><b>{p['name']}</b></td><td>{p['position']}</td></tr>" #<td>${p['price']}</td>
                    for p in team.get("players", [])
                )
                sub = f" ({team['full_name']})" if "full_name" in team else ""
                st.markdown(
                    f"<div class='g-card'><div class='g-card-title'>{team['badge']} {team['name']}{sub}</div>"
                    f"<table class='g-table'><thead><tr><th class='left'>Player</th><th>Pos</th></tr></thead>" #<th>Price</th>
                    f"<tbody>{rows}</tbody></table></div>",
                    unsafe_allow_html=True
                )

else:
    pwd = st.sidebar.text_input("Admin Password", type="password")
    if pwd != ADMIN_PASSWORD:
        st.warning("Enter the admin password in the sidebar to unlock controls.")
        st.stop()

    st.success("Admin Mode Unlocked")
    adm_tab1, adm_tab2 = st.tabs(["📝 Update Match & Events", "👥 Manage Teams & Players"])

    with adm_tab1:
        match_labels = {
            f"Day {m['matchday']}: {m['team1']} vs {m['team2']} ({m['id']})": m
            for m in data["matches"]
        }
        sel_label = st.selectbox("Select Match", list(match_labels.keys()))
        sel_match = match_labels[sel_label]

        c1, c2, c3 = st.columns(3)
        all_team_names = [t["name"] for t in data["teams"]] + ["1st Place", "2nd Place"]

        with c1:
            if sel_match["stage"] == "The Final":
                sel_match["team1"] = st.selectbox("Team 1", all_team_names, index=all_team_names.index(sel_match["team1"]) if sel_match["team1"] in all_team_names else 0)
            s1_val = st.number_input(f"{sel_match['team1']} Score", min_value=0, value=int(sel_match["score1"] or 0))
        with c2:
            if sel_match["stage"] == "The Final":
                sel_match["team2"] = st.selectbox("Team 2", all_team_names, index=all_team_names.index(sel_match["team2"]) if sel_match["team2"] in all_team_names else 0)
            s2_val = st.number_input(f"{sel_match['team2']} Score", min_value=0, value=int(sel_match["score2"] or 0))
        with c3:
            status_opts = ["Upcoming", "LIVE", "FT"]
            new_status = st.selectbox("Match Status", status_opts, index=status_opts.index(sel_match["status"]))

        if st.button("💾 Save Match Score & Status", type="primary"):
            sel_match["status"] = new_status
            sel_match["score1"] = None if new_status == "Upcoming" else s1_val
            sel_match["score2"] = None if new_status == "Upcoming" else s2_val
            save_data(data)
            st.toast("Match score saved!")
            st.rerun()

        st.divider()
        st.subheader("Match Events (Goals & Cards)")

        for idx, ev in enumerate(sel_match.get("events", [])):
            ec1, ec2 = st.columns([4, 1])
            ec1.write(f"**{ev['type'].upper()}** — {ev['player']} ({ev['team']})")
            if ec2.button("🗑️ Remove", key=f"del_ev_{idx}"):
                sel_match["events"].pop(idx)
                save_data(data)
                st.rerun()

        st.markdown("#### Add New Event")
        ev_c1, ev_c2, ev_c3 = st.columns(3)
        ev_team = ev_c1.selectbox("Team", [sel_match["team1"], sel_match["team2"]])
        ev_type = ev_c2.selectbox("Event Type", ["goal", "own_goal", "yellow", "red"])

        team_obj = next((t for t in data["teams"] if t["name"] == ev_team), None)
        player_opts = [p["name"] for p in team_obj.get("players", [])] if team_obj else []
        player_opts.append(f"Own Goal ({sel_match['team1']})")
        player_opts.append(f"Own Goal ({sel_match['team2']})")

        ev_player = ev_c3.selectbox("Player", player_opts)

        if st.button("➕ Add Event"):
            sel_match.setdefault("events", []).append({
                "type": ev_type,
                "team": ev_team,
                "player": ev_player
            })
            save_data(data)
            st.rerun()

        st.divider()
        st.download_button(
        label="⬇️ Click this to download the updated tournament.json file after making your changes, so that you can use it later as a backup.",
        data= json.dumps(data, indent=2, ensure_ascii=False),
        file_name="tournament.json",
        mime="application/json"
    )

    with adm_tab2:
        team_names = [t["name"] for t in data["teams"]]
        sel_t_name = st.selectbox("Select Team to Edit", team_names)
        sel_team = next(t for t in data["teams"] if t["name"] == sel_t_name)

        for idx, p in enumerate(sel_team.get("players", [])):
            pc1, pc2 = st.columns([4, 1])
            pc1.write(f"**{p['name']}** · {p['position']} · ${p['price']}")
            if pc2.button("Remove", key=f"del_p_{idx}"):
                sel_team["players"].pop(idx)
                save_data(data)
                st.rerun()

        with st.form("add_player_form"):
            st.markdown("#### Add Player")
            np_name = st.text_input("Player Name")
            np_pos = st.selectbox("Position", ["Forward", "Midfielder", "Defender", "Goalkeeper"])
            np_price = st.number_input("Price ($)", min_value=0, step=10)
            if st.form_submit_button("Add Player") and np_name:
                sel_team.setdefault("players", []).append({
                    "name": np_name, "position": np_pos, "price": np_price
                })
                save_data(data)
                st.rerun()

