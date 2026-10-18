"""
Real-Time Market Discrepancy & Arbitrage Engine
Author: YSL
Description: An automated pipeline that monitors live sports derivative markets, 
calculates cross-book consensus medians, and dispatches actionable +EV trade signals.
"""

import os
import json
import statistics
import requests

# =====================================================================
# 1. CONFIGURATION & ENVIRONMENT SETUP
# =====================================================================
# Uses environment variables for security, with fallback placeholders
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "YOUR_ODDS_API_KEY_HERE")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "YOUR_DISCORD_WEBHOOK_URL_HERE")

SPORT = "americanfootball_nfl"
MARKETS = "player_pass_yds,player_rush_yds,player_reception_yds"
DISCREPANCY_THRESHOLD = 3.5  # Minimum yardage variance required to trigger an alert


# =====================================================================
# 2. DATA FORMATTING & HELPER UTILITIES
# =====================================================================
def format_american_odds(price):
    """Formats numeric odds into clean American moneyline notation (+105, -115)."""
    if price is None:
        return "N/A"
    try:
        val = int(price)
        return f"+{val}" if val > 0 else str(val)
    except (ValueError, TypeError):
        return str(price)


def dispatch_discord_alert(payload_message):
    """Transmits real-time trade signals to Discord via asynchronous webhook."""
    if "YOUR_DISCORD" in DISCORD_WEBHOOK_URL:
        print("[Alert Skipped]: Set a valid Discord Webhook URL to receive alerts.")
        return

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": payload_message}, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[Network Error]: Failed to dispatch Discord alert: {e}")


# =====================================================================
# 3. QUANTITATIVE CONSENSUS & DISCREPANCY LOGIC
# =====================================================================
def audit_player_market(player_name, market_name, matchup, sportsbooks):
    """
    Evaluates individual player prop lines against multi-book market consensus
    to isolate pricing inefficiencies on target retail books (DraftKings & FanDuel).
    """
    dk_data = sportsbooks.get("draftkings")
    fd_data = sportsbooks.get("fanduel")

    # We must have at least one execution target active
    if not dk_data and not fd_data:
        return None

    # Aggregate lines across all available market makers to compute the true median
    all_points = [
        book["point"] for book in sportsbooks.values() 
        if book.get("point") is not None
    ]

    # Require at least 2 books to establish an objective market benchmark
    if len(all_points) < 2:
        return None

    consensus_line = round(statistics.median(all_points), 1)
    dk_pt = dk_data.get("point") if dk_data else None
    fd_pt = fd_data.get("point") if fd_data else None

    # If both primary retail targets have posted lines, check for divergence
    if dk_pt is not None and fd_pt is not None:
        diff = round(abs(dk_pt - fd_pt), 1)

        if diff >= DISCREPANCY_THRESHOLD:
            # Isolate which bookmaker diverged from the true market median
            if abs(dk_pt - consensus_line) > abs(fd_pt - consensus_line):
                target_book = "DraftKings"
                if dk_pt < consensus_line:
                    recommendation = f"BET OVER ON DRAFTKINGS ({dk_pt} @ {format_american_odds(dk_data.get('over_price'))})"
                    reason = f"DraftKings is {round(consensus_line - dk_pt, 1)} yds BELOW market consensus ({consensus_line})!"
                else:
                    recommendation = f"BET UNDER ON DRAFTKINGS ({dk_pt} @ {format_american_odds(dk_data.get('under_price'))})"
                    reason = f"DraftKings is {round(dk_pt - consensus_line, 1)} yds ABOVE market consensus ({consensus_line})!"
            else:
                target_book = "FanDuel"
                if fd_pt < consensus_line:
                    recommendation = f"BET OVER ON FANDUEL ({fd_pt} @ {format_american_odds(fd_data.get('over_price'))})"
                    reason = f"FanDuel is {round(consensus_line - fd_pt, 1)} yds BELOW market consensus ({consensus_line})!"
                else:
                    recommendation = f"BET UNDER ON FANDUEL ({fd_pt} @ {format_american_odds(fd_data.get('under_price'))})"
                    reason = f"FanDuel is {round(fd_pt - consensus_line, 1)} yds ABOVE market consensus ({consensus_line})!"

            # Construct clean notification payload
            dk_str = f"{dk_pt} (Over {format_american_odds(dk_data.get('over_price'))} | Under {format_american_odds(dk_data.get('under_price'))})"
            fd_str = f"{fd_pt} (Over {format_american_odds(fd_data.get('over_price'))} | Under {format_american_odds(fd_data.get('under_price'))})"

            return (
                f"🎯 **HIGH-CONVICTION BET FOUND**\n"
                f"**Player:** {player_name} ({market_name.replace('_', ' ').title()})\n"
                f"**Matchup:** {matchup}\n\n"
                f"📊 **Market Consensus:** {consensus_line} Yards (across {len(all_points)} books)\n"
                f"• **DraftKings:** {dk_str}\n"
                f"• **FanDuel:** {fd_str}\n\n"
                f"🚀 **ACTION:** 👉 **{recommendation}**\n"
                f"💡 **Why:** {reason}\n"
                f"--------------------------------------"
            )

    return None


# =====================================================================
# 4. PIPELINE EXECUTION ENGINE
# =====================================================================
def run_pipeline():
    """Main pipeline execution: handles API ingestion, parsing, and dispatching."""
    print("🚀 Initializing Market Discrepancy & Arbitrage Engine...")

    # Step 1: Fetch active schedule
    events_url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events"
    try:
        events_res = requests.get(events_url, params={"apiKey": ODDS_API_KEY}, timeout=10).json()
    except Exception as e:
        print(f"[Error]: Failed to query active schedule: {e}")
        return

    if not isinstance(events_res, list):
        print(f"[API Response Error]: {events_res}")
        return

    print(f"Ingested {len(events_res)} active matchups. Commencing cross-book audit...\n")
    alerts_triggered = 0

    # Step 2: Iterate through each event and extract derivative prop markets
    for event in events_res:
        game_id = event["id"]
        matchup = f"{event['away_team']} @ {event['home_team']}"

        odds_url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/events/{game_id}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": MARKETS,
            "oddsFormat": "american"
        }

        try:
            prop_data = requests.get(odds_url, params=params, timeout=10).json()
        except requests.exceptions.RequestException:
            continue

        bookmakers = {b["key"]: b for b in prop_data.get("bookmakers", [])}
        if "draftkings" not in bookmakers and "fanduel" not in bookmakers:
            continue

        # Build dynamic registry: market_registry[market_key][player_name][bookmaker]
        market_registry = {}

        for bm_key, bm_obj in bookmakers.items():
            for market in bm_obj.get("markets", []):
                m_key = market["key"]
                if m_key not in market_registry:
                    market_registry[m_key] = {}

                for outcome in market.get("outcomes", []):
                    player = outcome.get("description", "Unknown")
                    side = outcome.get("name", "Over")

                    if player not in market_registry[m_key]:
                        market_registry[m_key][player] = {}
                    if bm_key not in market_registry[m_key][player]:
                        market_registry[m_key][player][bm_key] = {}

                    market_registry[m_key][player][bm_key]["point"] = outcome.get("point")
                    market_registry[m_key][player][bm_key][f"{side.lower()}_price"] = outcome.get("price")

        # Step 3: Run quantitative consensus audit on compiled registry
        for m_key, player_dict in market_registry.items():
            for player_name, sportsbooks in player_dict.items():
                alert_text = audit_player_market(player_name, m_key, matchup, sportsbooks)
                if alert_text:
                    alerts_triggered += 1
                    print(alert_text)
                    dispatch_discord_alert(alert_text)

    print(f"\nAudit complete. Triggered {alerts_triggered} high-conviction trade signals.")


if __name__ == "__main__":
    run_pipeline()
