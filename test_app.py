import pandas as pd
from app import DataAnalystAgent


def test_profile_generation():
    df = pd.DataFrame({"sales": [100, 200], "region": ["North", "South"]})
    agent = DataAnalystAgent(api_key="test")
    profile = agent.get_profile(df)
    assert "Rows: 2" in profile
    assert "sales" in profile


def test_insights_without_key():
    df = pd.DataFrame({"sales": [100, 200]})
    agent = DataAnalystAgent(api_key="")
    insights = agent.generate_insights(df, "Find trends")
    assert "Please provide" in insights


def test_visualizations_created():
    df = pd.DataFrame({"region": ["North", "South", "North"], "sales": [100, 200, 150]})
    agent = DataAnalystAgent(api_key="test")
    figures = agent.create_visualizations(df)
    assert len(figures) >= 1
