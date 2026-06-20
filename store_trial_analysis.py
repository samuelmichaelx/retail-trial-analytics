import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

def main():
    print("Loading data...")
    df = pd.read_csv('QVI_data.csv')
    df['DATE'] = pd.to_datetime(df['DATE'])
    df['YEAR_MONTH'] = df['DATE'].dt.strftime('%Y%m')

    #1 Calculate monthly metrics per store
    monthly_metrics = df.groupby(['STORE_NBR', 'YEAR_MONTH']).agg(
        tot_sales=('TOT_SALES', 'sum'),
        n_customers=('LYLTY_CARD_NBR', 'nunique'), 
        n_txns=('TXN_ID', 'nunique')
    ).reset_index()

    # Filter for stores that have all 12 months of data
    months_per_store = monthly_metrics.groupby('STORE_NBR')['YEAR_MONTH'].count()
    full_stores = months_per_store[months_per_store == 12].index
    monthly_metrics_filtered = monthly_metrics[monthly_metrics['STORE_NBR'].isin(full_stores)]

    #2 Control store selection (Pre-trial: July 2018 - Jan 2019)
    pre_trial = monthly_metrics[monthly_metrics['YEAR_MONTH'] < '201902'].reset_index(drop=True)
    trial_stores = [77, 86, 88]
    control_pairs = {}

    print("Identifying control stores...")
    for trial in trial_stores:
        trial_data = pre_trial[pre_trial['STORE_NBR'] == trial]
        best_score = -1
        best_control = None

        other_stores = pre_trial['STORE_NBR'].unique()
        other_stores = other_stores[other_stores != trial]

        for control in other_stores:
            control_data = pre_trial[pre_trial['STORE_NBR'] == control]

            #calculate correlation for each metric
            corr_sales = trial_data['tot_sales'].reset_index(drop=True).corr(control_data['tot_sales'].reset_index(drop=True))
            cust_corr = trial_data['n_customers'].reset_index(drop=True).corr(control_data['n_customers'].reset_index(drop=True))

            #Composite score (simplification of matching)
            if pd.notna(corr_sales) and pd.notna(cust_corr):
                score = (corr_sales + cust_corr) / 2
                if score > best_score:
                    best_score = score
                    best_control = control

        control_pairs[trial] = best_control
        print(f"Trial Store {trial} matched with Control Store {best_control} (Score: {best_score:.2f})")

        #Assesment Visualization
        print("Generating visualization...")
        trial_start, trial_end = '201902', '201904'
    fig, axes = plt.subplots(3, 2, figsize=(15, 15))
    fig.tight_layout(pad=6.0)

    metrics = [('tot_sales', 'Total Sales ($)'), ('n_customers', 'Number of Customers')]

    for i, (trial, control) in enumerate(control_pairs.items()):
        for j, (metric, metric_name) in enumerate(metrics):
            t_data = monthly_metrics[monthly_metrics['STORE_NBR'] == trial].sort_values('YEAR_MONTH').reset_index(drop=True)
            c_data = monthly_metrics[monthly_metrics['STORE_NBR'] == control].sort_values('YEAR_MONTH').reset_index(drop=True)
            
            # Scale control data to align with trial store baseline
            scaling_factor = t_data[t_data['YEAR_MONTH'] < trial_start][metric].sum() / c_data[c_data['YEAR_MONTH'] < trial_start][metric].sum()
            c_data[f'scaled_{metric}'] = c_data[metric] * scaling_factor
            
            ax = axes[i, j]
            x_labels = [str(x)[4:6] + '/' + str(x)[0:4] for x in t_data['YEAR_MONTH']]
            ax.plot(x_labels, t_data[metric], label=f'Trial {trial}', marker='o')
            ax.plot(x_labels, c_data[f'scaled_{metric}'], label=f'Control {control}', marker='x', linestyle='--')
            ax.axvspan('02/2019', '04/2019', color='yellow', alpha=0.3, label='Trial Period')
            
            ax.set_title(f'{metric_name}: Store {trial} vs {control}')
            ax.tick_params(axis='x', rotation=45)
            ax.legend()

    plt.savefig('trial_performance.png', bbox_inches='tight')
    print("Analysis complete. Visualizations saved as 'trial_performance.png'.")

if __name__ == "__main__":
    main()

                       
                        