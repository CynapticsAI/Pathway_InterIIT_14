import pickle
import os
from datetime import datetime

MODELS_DIR = "models"

SECTOR_TICKERS = {
    "Energy": "XLE",
    "Materials": "XLB",
    "Industrials": "XLI",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Health Care": "XLV",
    "Financials": "XLF",
    "Information Technology": "XLK",
    "Communication Services": "XLC",
    "Utilities": "XLU",
    "Real Estate": "XLRE"
}


def load_model(sector: str):
    """Load a trained model from disk"""
    filename = f"{MODELS_DIR}/{sector.replace(' ', '_')}_model.pkl"
    
    if not os.path.exists(filename):
        return None
    
    with open(filename, 'rb') as f:
        model_data = pickle.load(f)
    
    return model_data


def format_metric(value, decimals=4):
    """Format a metric value for display"""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def main():
    print("=" * 80)
    print("STOCK SECTOR MODEL METRICS")
    print("=" * 80)
    print()
    
    if not os.path.exists(MODELS_DIR):
        print(f"Error: '{MODELS_DIR}/' directory not found.")
        print("Please ensure trained models exist in the models/ directory.")
        return
    
    loaded_models = {}
    
    for sector in SECTOR_TICKERS.keys():
        model_data = load_model(sector)
        if model_data:
            loaded_models[sector] = model_data
    
    if not loaded_models:
        print("No models found in the models/ directory.")
        return
    
    print(f"Loaded {len(loaded_models)}/{len(SECTOR_TICKERS)} models\n")
    
    print("-" * 80)
    print(f"{'SECTOR':<28} {'TICKER':<8} {'RMSE':<10} {'MAE':<10} {'DIR ACC':<10} {'TRAINED'}")
    print("-" * 80)
    
    all_metrics = []
    
    for sector, model_data in loaded_models.items():
        ticker = SECTOR_TICKERS[sector]
        metrics = model_data.get('metrics', {})
        timestamp = model_data.get('timestamp', 'Unknown')
        
        rmse = metrics.get('test_rmse')
        mae = metrics.get('test_mae')
        dir_acc = metrics.get('test_dir_acc')
        
        all_metrics.append({
            'sector': sector,
            'ticker': ticker,
            'rmse': rmse,
            'mae': mae,
            'dir_acc': dir_acc,
            'timestamp': timestamp
        })
        
        if isinstance(timestamp, str) and len(timestamp) > 19:
            timestamp = timestamp[:19]
        
        print(f"{sector:<28} {ticker:<8} {format_metric(rmse):<10} {format_metric(mae):<10} {format_metric(dir_acc):<10} {timestamp}")
    
    print("-" * 80)
    
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    valid_rmse = [m['rmse'] for m in all_metrics if m['rmse'] is not None]
    valid_mae = [m['mae'] for m in all_metrics if m['mae'] is not None]
    valid_dir_acc = [m['dir_acc'] for m in all_metrics if m['dir_acc'] is not None]
    
    if valid_rmse:
        print(f"\nRMSE (Root Mean Square Error):")
        print(f"  Average: {sum(valid_rmse)/len(valid_rmse):.4f}")
        print(f"  Best:    {min(valid_rmse):.4f}")
        print(f"  Worst:   {max(valid_rmse):.4f}")
    
    if valid_mae:
        print(f"\nMAE (Mean Absolute Error):")
        print(f"  Average: {sum(valid_mae)/len(valid_mae):.4f}")
        print(f"  Best:    {min(valid_mae):.4f}")
        print(f"  Worst:   {max(valid_mae):.4f}")
    
    if valid_dir_acc:
        print(f"\nDirectional Accuracy (% correct direction predictions):")
        print(f"  Average: {sum(valid_dir_acc)/len(valid_dir_acc)*100:.2f}%")
        print(f"  Best:    {max(valid_dir_acc)*100:.2f}%")
        print(f"  Worst:   {min(valid_dir_acc)*100:.2f}%")
    
    if valid_dir_acc:
        sorted_by_acc = sorted(all_metrics, key=lambda x: x['dir_acc'] or 0, reverse=True)
        
        print(f"\nBest Performing Models (by Directional Accuracy):")
        for i, m in enumerate(sorted_by_acc[:3], 1):
            if m['dir_acc']:
                print(f"  {i}. {m['sector']} ({m['ticker']}): {m['dir_acc']*100:.2f}%")
        
        print(f"\nWorst Performing Models (by Directional Accuracy):")
        for i, m in enumerate(sorted_by_acc[-3:], 1):
            if m['dir_acc']:
                print(f"  {i}. {m['sector']} ({m['ticker']}): {m['dir_acc']*100:.2f}%")
    
    print("\n" + "=" * 80)
    print("MODEL DETAILS")
    print("=" * 80)
    
    for sector, model_data in loaded_models.items():
        print(f"\n{sector} ({SECTOR_TICKERS[sector]})")
        print("-" * 40)
        
        features = model_data.get('features', [])
        print(f"  Features ({len(features)} total):")
        
        base_features = set()
        for f in features:
            base = f.split('_lag')[0].split('_ma')[0].split('_std')[0].split('_roc')[0]
            base_features.add(base)
        print(f"    Base FRED series: {', '.join(sorted(base_features))}")
        
        if 'model_config' in model_data:
            config = model_data['model_config']
            print(f"  Model Config:")
            print(f"    Input dim:   {config.get('input_dim', 'N/A')}")
            print(f"    Hidden dim:  {config.get('hidden_dim', 'N/A')}")
            print(f"    Num layers:  {config.get('num_layers', 'N/A')}")
            print(f"    Dropout:     {config.get('dropout', 'N/A')}")
        
        seq_len = model_data.get('sequence_length')
        if seq_len:
            print(f"  Sequence length: {seq_len}")
        
        last_data = model_data.get('last_data_date')
        if last_data:
            print(f"  Last data date: {last_data}")
    
    print("\n" + "=" * 80)
    print("Done!")


if __name__ == "__main__":
    main()