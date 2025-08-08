#!/usr/bin/env python3
"""
Test the scientifically corrected velocity threshold (0.933) for ETHOSCOPE_018.
Compare sleep patterns with ETHOSCOPE_072 using default threshold (1.0).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from ethoscopy.load import load_ethoscope, link_meta_index
from ethoscopy.analyse import sleep_annotation, max_velocity_detector


def test_corrected_threshold():
    """Test the corrected velocity threshold and compare results."""

    # Load metadata
    metadata_file = (
        "/home/gg/Code/db_samples/tmp/metadata_84C10-AD_23E10-DBD_Suvar3_9_SD_0801.csv"
    )
    db_dir = "/home/gg/Code/db_samples/tmp/"
    metadata_linked = link_meta_index(metadata_file, db_dir)

    # Get sample animals from each machine
    animals_018 = metadata_linked[
        metadata_linked["machine_name"] == "ETHOSCOPE_018"
    ].head(2)
    animals_072 = metadata_linked[
        metadata_linked["machine_name"] == "ETHOSCOPE_072"
    ].head(2)

    print("=== Testing Corrected Velocity Threshold ===")

    def load_with_threshold(animals, threshold, machine_name):
        """Load data with specific velocity threshold."""

        def custom_motion_detector(
            data, time_window_length, masking_duration=6, velocity_correction_coef=3e-3
        ):
            return max_velocity_detector(
                data,
                time_window_length=time_window_length,
                velocity_threshold=threshold,
                walk_threshold=threshold + 1.5,
                velocity_correction_coef=velocity_correction_coef,
                masking_duration=masking_duration,
            )

        def custom_sleep_annotation(data):
            return sleep_annotation(
                data,
                time_window_length=10,
                motion_detector_function=custom_motion_detector,
                velocity_correction_coef=3e-3,
            )

        print(f"Loading {machine_name} with velocity_threshold={threshold}...")
        data = load_ethoscope(animals, FUN=custom_sleep_annotation)
        return data

    # Test configurations
    configs = [
        (animals_018, 1.0, "ETHOSCOPE_018 (default threshold=1.0)"),
        (animals_018, 0.933, "ETHOSCOPE_018 (corrected threshold=0.933)"),
        (animals_072, 1.0, "ETHOSCOPE_072 (default threshold=1.0)"),
    ]

    results = {}

    for animals, threshold, label in configs:
        data = load_with_threshold(animals, threshold, label)

        if data is not None and len(data) > 0:
            # Calculate key metrics
            sleep_pct = data["asleep"].mean() * 100
            movement_pct = data["moving"].mean() * 100

            # Velocity statistics
            max_vel_mean = data["max_velocity"].mean()
            max_vel_std = data["max_velocity"].std()
            max_vel_median = data["max_velocity"].median()

            results[label] = {
                "data": data,
                "sleep_percentage": sleep_pct,
                "movement_percentage": movement_pct,
                "max_velocity_mean": max_vel_mean,
                "max_velocity_std": max_vel_std,
                "max_velocity_median": max_vel_median,
                "total_points": len(data),
            }

            print(f"\n{label}:")
            print(f"  Total data points: {len(data)}")
            print(f"  Sleep: {sleep_pct:.1f}%")
            print(f"  Movement: {movement_pct:.1f}%")
            print(
                f"  Max velocity - Mean: {max_vel_mean:.3f}, Median: {max_vel_median:.3f}, Std: {max_vel_std:.3f}"
            )
        else:
            print(f"\n{label}: Failed to load data")

    # Compare results
    if len(results) >= 3:
        print(f"\n=== COMPARISON RESULTS ===")

        original_018 = results["ETHOSCOPE_018 (default threshold=1.0)"]
        corrected_018 = results["ETHOSCOPE_018 (corrected threshold=0.933)"]
        reference_072 = results["ETHOSCOPE_072 (default threshold=1.0)"]

        print(f"Sleep percentage comparison:")
        print(f"  ETHOSCOPE_018 (original):  {original_018['sleep_percentage']:6.1f}%")
        print(f"  ETHOSCOPE_018 (corrected): {corrected_018['sleep_percentage']:6.1f}%")
        print(f"  ETHOSCOPE_072 (reference): {reference_072['sleep_percentage']:6.1f}%")

        improvement = (
            corrected_018["sleep_percentage"] - original_018["sleep_percentage"]
        )
        similarity_to_072 = abs(
            corrected_018["sleep_percentage"] - reference_072["sleep_percentage"]
        )

        print(f"\nImprovement metrics:")
        print(f"  Sleep increase for 018: {improvement:+.1f} percentage points")
        print(f"  Difference from 072: {similarity_to_072:.1f} percentage points")

        # Check if corrected 018 is closer to 072 than original 018
        original_diff = abs(
            original_018["sleep_percentage"] - reference_072["sleep_percentage"]
        )
        corrected_diff = abs(
            corrected_018["sleep_percentage"] - reference_072["sleep_percentage"]
        )

        if corrected_diff < original_diff:
            print(
                f"  ✓ Corrected threshold brings ETHOSCOPE_018 closer to ETHOSCOPE_072 behavior"
            )
        else:
            print(f"  ✗ Correction did not improve similarity to ETHOSCOPE_072")

    # Create visualization
    if len(results) >= 2:
        create_comparison_plots(results)

    return results


def create_comparison_plots(results):
    """Create plots comparing the different configurations."""

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Plot 1: Sleep percentage comparison
    labels = list(results.keys())
    sleep_values = [results[label]["sleep_percentage"] for label in labels]

    bars = axes[0, 0].bar(
        range(len(labels)), sleep_values, color=["red", "green", "blue"][: len(labels)]
    )
    axes[0, 0].set_xlabel("Configuration")
    axes[0, 0].set_ylabel("Sleep Percentage (%)")
    axes[0, 0].set_title("Sleep Percentage Comparison")
    axes[0, 0].set_xticks(range(len(labels)))
    axes[0, 0].set_xticklabels(
        [label.split("(")[0].strip() for label in labels], rotation=45
    )

    # Add value labels on bars
    for bar, value in zip(bars, sleep_values):
        axes[0, 0].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
        )

    # Plot 2: Velocity distribution comparison
    colors = ["red", "green", "blue"]
    for i, (label, result) in enumerate(results.items()):
        if "data" in result:
            axes[0, 1].hist(
                result["data"]["max_velocity"],
                bins=30,
                alpha=0.6,
                label=label.split("(")[0].strip(),
                color=colors[i],
                density=True,
            )

    axes[0, 1].set_xlabel("Max Velocity")
    axes[0, 1].set_ylabel("Density")
    axes[0, 1].set_title("Velocity Distribution Comparison")
    axes[0, 1].legend()
    axes[0, 1].set_xlim(0, 10)

    # Plot 3: Movement percentage comparison
    movement_values = [results[label]["movement_percentage"] for label in labels]
    bars = axes[1, 0].bar(
        range(len(labels)),
        movement_values,
        color=["red", "green", "blue"][: len(labels)],
    )
    axes[1, 0].set_xlabel("Configuration")
    axes[1, 0].set_ylabel("Movement Percentage (%)")
    axes[1, 0].set_title("Movement Percentage Comparison")
    axes[1, 0].set_xticks(range(len(labels)))
    axes[1, 0].set_xticklabels(
        [label.split("(")[0].strip() for label in labels], rotation=45
    )

    for bar, value in zip(bars, movement_values):
        axes[1, 0].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
        )

    # Plot 4: Summary statistics table
    summary_data = []
    for label, result in results.items():
        summary_data.append(
            [
                label.split("(")[0].strip(),
                f"{result['sleep_percentage']:.1f}%",
                f"{result['movement_percentage']:.1f}%",
                f"{result['max_velocity_mean']:.2f}",
                f"{result['total_points']:,}",
            ]
        )

    table = axes[1, 1].table(
        cellText=summary_data,
        colLabels=["Machine", "Sleep %", "Movement %", "Avg Velocity", "Data Points"],
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    axes[1, 1].axis("off")
    axes[1, 1].set_title("Summary Statistics")

    plt.tight_layout()
    plt.savefig("corrected_threshold_comparison.png", dpi=300, bbox_inches="tight")
    print(f"\nPlots saved to: corrected_threshold_comparison.png")
    plt.show()


if __name__ == "__main__":
    results = test_corrected_threshold()
