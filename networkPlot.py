import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def plot_log_log_degree_distribution(csv_file):
    try:
        df = pd.read_csv(csv_file)

        if "Degree" not in df.columns or df.empty:
            print("Error: 'Degree' column missing or empty dataset.")
            return

        df["Degree"] = pd.to_numeric(df["Degree"], errors="coerce").fillna(0).astype(int)
        degrees = df["Degree"]
        # print(degrees)
        if degrees.empty:
            print("No valid degree data available.")
            return

        # Compute histogram bins in log scale
        min_degree = max(1, degrees.min())  # Avoid log(0)
        max_degree = degrees.max()
        bins = np.logspace(np.log10(min_degree), np.log10(max_degree), num=20)  # Log-spaced bins

        # Histogram
        hist, bin_edges = np.histogram(degrees, bins=bins)
        
        # Convert bin centers for plotting
        bin_centers = np.sqrt(bin_edges[:-1] * bin_edges[1:])  # Geometric mean of bin edges

        plt.figure(figsize=(10, 6))
        plt.scatter(bin_centers, hist, color="blue", alpha=0.7, label="Degree Distribution")
        plt.xscale("log")
        plt.yscale("log")
        plt.title("Log-Log Degree Distribution of the Network", fontsize=16)
        plt.xlabel("Degree (log scale)", fontsize=14)
        plt.ylabel("Number of Peers (log scale)", fontsize=14)
        plt.grid(True, which="both", linestyle="--", alpha=0.7)
        plt.legend()
        plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function
plot_log_log_degree_distribution("peer_list.csv")
