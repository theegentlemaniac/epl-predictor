import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os

def scrape_premier_league_data(years=[2024, 2023]):
    """Scrape Premier League match data from FBRef."""
    prem_team_matches = []
    prem_standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
    
    for year in years:
        print(f"Scraping data for {year} season...")
        
        data = requests.get(prem_standings_url)
        soup = BeautifulSoup(data.text, 'html.parser')
        time.sleep(5)  # Respectful delay between requests
        
        prem_standings_table = soup.select('table.stats_table')[0]
        team_links = [l.get("href") for l in prem_standings_table.find_all('a') if '/squads/' in l]
        team_urls = [f"https://fbref.com{l}" for l in team_links]
        
        previous_season = soup.select("a.prev")[0].get("href")
        prem_standings_url = f"https://fbref.com{previous_season}"
        
        for team_url in team_urls:
            team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
            print(f"  Scraping {team_name}...")
            
            try:
                # Get matches data
                team_data = requests.get(team_url)
                matches = pd.read_html(team_data.text, match="Scores & Fixtures")[0]
                time.sleep(5)
                
                # Get additional stats
                temp_soup = BeautifulSoup(team_data.text, 'html.parser')
                temp_links = [l.get("href") for l in temp_soup.find_all('a') if 'all_comps/shooting/' in l]
                
                if not temp_links:
                    continue
                    
                shooting_data = requests.get(f"https://fbref.com{temp_links[0]}")
                shooting = pd.read_html(shooting_data.text, match="Shooting")[0]
                shooting.columns = shooting.columns.droplevel()
                
                # Merge data
                team_matches = matches.merge(
                    shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], 
                    on="Date"
                )
                
                # Filter and add metadata
                team_matches = team_matches[team_matches["Comp"] == "Premier League"]
                team_matches["Season"] = year
                team_matches["Team"] = team_name
                team_matches["ScrapedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                prem_team_matches.append(team_matches)
                time.sleep(5)
                
            except Exception as e:
                print(f"Error scraping {team_name}: {str(e)}")
                continue
    
    # Combine all data
    match_df = pd.concat(prem_team_matches)
    match_df.columns = [c.lower() for c in match_df.columns]
    
    # Clean data
    match_df['date'] = pd.to_datetime(match_df['date'])
    match_df.sort_values(['date', 'team'], inplace=True)
    
    # Ensure data directory exists
    os.makedirs('backend/data', exist_ok=True)
    
    # Save to CSV
    match_df.to_csv("backend/data/prem_matches.csv", index=False)
    print("Data scraping complete!")
    return match_df

if __name__ == "__main__":
    df = scrape_premier_league_data()
