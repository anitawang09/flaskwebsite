import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
import json

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DB_PATH = os.path.join(BASE_DIR, 'cleaned_data.db')

def load_emissions_data():
    """Load and preprocess greenhouse gas emissions data"""
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql('SELECT * FROM greenhouse_gas_emissions', conn)
    
    # Convert and extract temporal features
    df['Quarter'] = pd.to_datetime(df['Quarter'])
    df['Year'] = df['Quarter'].dt.year
    df['Quarter_Label'] = 'Q' + df['Quarter'].dt.quarter.astype(str)
    
    return df

def plot_quarterly_emissions_bar_chart(df):
    """Generate and save bar chart for quarterly emissions"""
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(data=df, x='Quarter_Label', y='GHG Emissions (MtCO2e)', 
                     palette='viridis', ci=None)
    ax.set(title='Quarterly Greenhouse Gas Emissions',
           xlabel='Quarter',
           ylabel='Emissions (MtCO₂e)')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_DIR, 'emissions_bar.png'), dpi=300)
    plt.close()

def plot_annual_quarterly_heatmap(df):
    """Generate and save heatmap for annual-quarterly emissions"""
    heatmap_data = df.pivot_table(index='Year', columns='Quarter_Label', 
                                  values='GHG Emissions (MtCO2e)', aggfunc='mean')
    plt.figure(figsize=(10, 8))
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlGnBu',
                cbar_kws={'label': 'Emissions (MtCO₂e)'})
    plt.title('Annual-Quarterly Emissions Patterns')
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_DIR, 'emissions_heatmap.png'), dpi=300)
    plt.close()

def plot_quarterly_trends_line_chart(df):
    """Generate and save line chart for quarterly emissions trends by gas type"""
    plt.figure(figsize=(14, 6))
    for gas in df['gas_type'].unique():
        subset = df[df['gas_type'] == gas]
        plt.plot(
            subset['Quarter'],
            subset['GHG Emissions (MtCO2e)'],
            label=gas,
            marker='o'
        )
    plt.title('Quarterly GHG Emissions Trends')
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(STATIC_DIR, 'quarterly_trends.png'), dpi=300)
    plt.close()


#visualization!#
def create_visualizations():
    """Generate and save all visualizations"""
    df = load_emissions_data()
    os.makedirs(STATIC_DIR, exist_ok=True)
    
    plot_quarterly_emissions_bar_chart(df)
    plot_annual_quarterly_heatmap(df)
    plot_quarterly_trends_line_chart(df)
    
    return {
        'bar_chart': 'emissions_bar.png',
        'heatmap': 'emissions_heatmap.png',
        'line_chart': 'quarterly_trends.png'
    }


def save_emissions_json(df, filename):
    payload = {
        "labels": df['continent'].tolist(),
        "data":   df['emission_rate'].tolist()
    }
    with open(os.path.join(STATIC_DIR, filename), 'w') as f:
        json.dump(payload, f, indent=2)



cont_df = get_continent_emissions('2024Q2')
save_emissions_json(cont_df, 'emissions_2024Q2.json')
print(json.dumps(payload, indent=2))