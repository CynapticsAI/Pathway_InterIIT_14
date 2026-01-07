import pathway as pw
from datetime import datetime
import panel as pn

# --- Bokeh Imports --
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
class MarketBreadthSchema(pw.Schema):
    timestamp: str  # Timestamps come as strings from JSON
    advancing_stocks: int
    declining_stocks: int
    unchanged_stocks: int
    total_stocks: int
    advance_decline_line: int


# --- 2. Bokeh Plotting Function (Unchanged) ---
def create_bokeh_plot(source: ColumnDataSource):
    """
    Creates a Bokeh figure for plotting market breadth.
    """
    plot = figure(
        height=400,
        width=800,
        title="Live Market Breadth",
        x_axis_label="Time",
        y_axis_label="Number of Stocks",
        x_axis_type="datetime"
    )
    plot.line('timestamp', 'advancing_stocks', source=source, legend_label="Advancing", color="green", line_width=2)
    plot.line('timestamp', 'declining_stocks', source=source, legend_label="Declining", color="red", line_width=2)
    plot.line('timestamp', 'unchanged_stocks', source=source, legend_label="Unchanged", color="grey", line_width=1,
              line_dash="dashed")

    plot.xaxis.formatter = DatetimeTickFormatter(
        hours="%H:%M:%S",
        minutes="%H:%M",
        days="%Y-%m-%d",
        months="%Y-%m",
        years="%Y"
    )
    plot.xaxis.major_label_orientation = 0.8
    plot.legend.location = "top_left"
    plot.legend.click_policy = "hide"
    return plot


# --- 3. Main Execution Function ---
def main():
    """Main function to run the Market Breadth *DASHBOARD*"""
    print("=" * 80)
    print("PATHWAY MARKET BREADTH DASHBOARD")
    print("=" * 80)

    # Connect to Kafka for the processed breadth data
    print("Connecting to Kafka for 'stock-signals' data...")
    breadth_data = pw.io.kafka.read(
        rdkafka_settings={
            "bootstrap.servers": "kafka:9092",
            "group.id": "stock_dashboard_consumer",  # Different group.id
            "session.timeout.ms": "6000",
        },
        topic="stock-signals",  # Read from the pipeline's output topic
        schema=MarketBreadthSchema,
        format="json",
        autocommit_duration_ms=1,
    )
    print("✅ Kafka 'stock-signals' stream connected.")

    # Convert timestamp string back to datetime for plotting
    # We must handle the fractional seconds
    breadth_data = breadth_data.with_columns(
        timestamp=pw.this.timestamp.dt.strptime(
            fmt="%Y-%m-%dT%H:%M:%S.%f"
        )
    )

    # --- Attach the Bokeh Plot ---
    print("\nConfiguring live Bokeh plot...")
    plot_widget = breadth_data.plot(create_bokeh_plot)

    pn.extension()
    dashboard = pn.Column(
        "## Live Market Breadth Analysis",
        plot_widget,
    )
    dashboard.servable()

    print("\nStarting stream processing and Bokeh server...")
    print("=" * 80)
    print("View the live plot in your browser (check terminal output for the URL, usually http://localhost:8001)")
    print("Press Ctrl+C in the terminal to stop...\n")

    # Run the dashboard
    pw.run()

    print("\nProcessing stopped.")
    print("=" * 80)


if __name__ == "__main__":
    main()
