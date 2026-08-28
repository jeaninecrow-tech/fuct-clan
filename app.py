import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="FAFO Clan Intel Dashboard", page_icon="🛡️", layout="wide"
)


@st.cache_data
def load_data():
  # Load directly from the Excel workbook using the MASTER sheet
  excel_path = "FAFO_Clan_Intel_2026-08-27_2.xlsx"
  try:
    # Row 0 is the description header, row 1 contains the actual column names in this workbook layout
    df = pd.read_excel(excel_path, sheet_name="MASTER", header=1)
  except Exception as e:
    st.error(f"Error loading Excel file: {e}")
    df = pd.DataFrame()
  return df


df = load_data()

# App Title & Overview
st.title("🛡️ FAFO Clan Intel: Interactive Command Center")
st.markdown(
    "_One source of truth, optimized for tracking player stats, clan depth,"
    " and rosters._"
)

if df.empty:
  st.warning(
      "Master data file not found or empty. Please ensure"
      " 'FAFO_Clan_Intel_2026-08-27_2.xlsx' is in your repository folder."
  )
else:
  # Clean up any potential unnamed columns or empty rows
  df = df.dropna(subset=["Player"]) if "Player" in df.columns else df

  # Sidebar Navigation
  st.sidebar.header("Navigation Menu")
  app_mode = st.sidebar.selectbox(
      "Choose a View",
      [
          "Dashboard & Scoreboard",
          "Player Card Lookup",
          "Clan Comparison",
          "Master Roster",
      ],
  )

  # Clean and parse columns safely
  if "Reso" in df.columns:
    df["Reso"] = pd.to_numeric(df["Reso"], errors="coerce").fillna(0)
  if "Combat\nRating" in df.columns:
    df["Combat\nRating"] = pd.to_numeric(
        df["Combat\nRating"], errors="coerce"
    ).fillna(0)
  if "Power\nIndex" in df.columns:
    df["Power\nIndex"] = pd.to_numeric(
        df["Power\nIndex"], errors="coerce"
    ).fillna(0)

  # ----------------------------------------------------
  # 1. DASHBOARD & SCOREBOARD
  # ----------------------------------------------------
  if app_mode == "Dashboard & Scoreboard":
    st.header("📊 Clan Scoreboard & Faction Overview")

    faction_filter = st.radio(
        "Filter Faction Switch:",
        ["ALL", "SHADOW", "IMMORTAL", "STANDALONE"],
        horizontal=True,
    )

    filtered_df = df.copy()
    if faction_filter != "ALL":
      if faction_filter == "STANDALONE":
        filtered_df = filtered_df[filtered_df["Faction"] == "STANDALONE"]
      else:
        filtered_df = filtered_df[
            (filtered_df["Faction"] == faction_filter)
            | (filtered_df["Faction"] == "STANDALONE")
        ]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Players in View", len(filtered_df))
    col2.metric("Clans Tracked", filtered_df["Clan"].nunique())
    col3.metric(
        "Avg Resonance",
        f"{filtered_df['Reso'].mean():,.0f}" if not filtered_df.empty else 0,
    )
    col4.metric(
        "10k+ Club Members",
        len(filtered_df[filtered_df["Reso"] >= 10000]),
    )

    st.markdown("---")
    st.subheader("Clan Summary Breakdown")

    if not filtered_df.empty:
      clan_summary = (
          filtered_df.groupby("Clan")
          .agg(
              Faction=("Faction", "first"),
              Members=("Player", "count"),
              Avg_Reso=("Reso", "mean"),
              Best_Reso=("Reso", "max"),
              Avg_CR=("Combat\nRating", "mean"),
              Avg_Power=("Power\nIndex", "mean"),
          )
          .reset_index()
      )

      clan_summary = clan_summary.sort_values(by="Avg_Reso", ascending=False)
      clan_summary["Avg_Reso"] = clan_summary["Avg_Reso"].round(0)
      clan_summary["Avg_CR"] = clan_summary["Avg_CR"].round(0)
      clan_summary["Avg_Power"] = clan_summary["Avg_Power"].round(1)

      st.dataframe(clan_summary, use_container_width=True)
    else:
      st.info("No data available for the selected filter.")

  # ----------------------------------------------------
  # 2. PLAYER CARD LOOKUP
  # ----------------------------------------------------
  elif app_mode == "Player Card Lookup":
    st.header("👤 Individual Player Card")

    player_list = sorted(df["Player"].dropna().unique().tolist())
    selected_player = st.selectbox("Pick a Player (A-Z):", player_list)

    if selected_player:
      p_data = df[df["Player"] == selected_player].iloc[0]

      col1, col2, col3 = st.columns(3)
      col1.metric("Clan", p_data.get("Clan", "N/A"))
      col2.metric(
          "Class / Role",
          f"{p_data.get('Class', 'N/A')} ({p_data.get('Role', 'N/A')})",
      )
      col3.metric("Faction", p_data.get("Faction", "N/A"))

      st.markdown("### Stat Line")
      sc1, sc2, sc3, sc4 = st.columns(4)
      sc1.metric("Resonance", f"{p_data.get('Reso', 0):,.0f}")
      sc2.metric("Combat Rating", f"{p_data.get('Combat\nRating', 0):,.0f}")
      sc3.metric("Secondary Avg", p_data.get("Secondary\navg (k)", "N/A"))
      sc4.metric("Power Index", p_data.get("Power\nIndex", "N/A"))

      st.info(
          f"**Reso Tier:** {p_data.get('Reso Tier', 'N/A')} | **Data Status:**"
          f" {p_data.get('Data Status', 'N/A')} | **Transfer Plan:**"
          f" {p_data.get('Transfer plan', 'None Specified')}"
      )

  # ----------------------------------------------------
  # 3. CLAN COMPARISON
  # ----------------------------------------------------
  elif app_mode == "Clan Comparison":
    st.header("⚔️ Head-to-Head Clan Comparison")

    clans = sorted(df["Clan"].dropna().unique().tolist())
    c1, c2 = st.columns(2)
    clan_a = c1.selectbox("Select Clan A:", clans, index=0 if clans else 0)
    clan_b = c2.selectbox(
        "Select Clan B:", clans, index=1 if len(clans) > 1 else 0
    )

    if clan_a and clan_b:
      df_a = df[df["Clan"] == clan_a]
      df_b = df[df["Clan"] == clan_b]

      comparison_data = {
          "Metric": [
              "Members Count",
              "Average Resonance",
              "Best Resonance",
              "Average Combat Rating",
              "Average Power Index",
          ],
          clan_a: [
              len(df_a),
              round(df_a["Reso"].mean(), 1),
              df_a["Reso"].max(),
              round(df_a["Combat\nRating"].mean(), 1),
              round(df_a["Power\nIndex"].mean(), 1),
          ],
          clan_b: [
              len(df_b),
              round(df_b["Reso"].mean(), 1),
              df_b["Reso"].max(),
              round(df_b["Combat\nRating"].mean(), 1),
              round(df_b["Power\nIndex"].mean(), 1),
          ],
      }
      comp_df = pd.DataFrame(comparison_data)
      st.dataframe(comp_df, use_container_width=True)

  # ----------------------------------------------------
  # 4. MASTER ROSTER VIEW
  # ----------------------------------------------------
  elif app_mode == "Master Roster":
    st.header("📋 Master Database Roster")
    search_query = st.text_input("Search Player Name:")

    view_df = df.copy()
    if search_query:
      view_df = view_df[
          view_df["Player"].str.contains(search_query, case=False, na=False)
      ]

    # Display clean subset of master columns
    cols_to_show = [
        c
        for c in [
            "Faction",
            "Clan",
            "Player",
            "Class",
            "Role",
            "Combat\nRating",
            "Reso",
            "Power\nIndex",
        ]
        if c in view_df.columns
    ]
    st.dataframe(view_df[cols_to_show], use_container_width=True)