#!/usr/bin/env python3
"""
Empirical testing of velocity thresholds for sleep annotation.
Tests different velocity_threshold values to find optimal parameters for each machine.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ethoscopy.analyse import sleep_annotation
from ethoscopy.load import link_meta_index, load_ethoscope


def test_velocity_thresholds():
    """Test range of velocity thresholds on sample data from both machines."""

    # Load metadata
    metadata_file = (
        "/home/gg/Code/db_samples/tmp/metadata_84C10-AD_23E10-DBD_Suvar3_9_SD_0801.csv"
    )
    db_dir = "/home/gg/Code/db_samples/tmp/"
    metadata_linked = link_meta_index(metadata_file, db_dir)

    # Get one animal from each machine for testing
    animals_018 = metadata_linked[
        metadata_linked["machine_name"] == "ETHOSCOPE_018"
    ].head(1)
    animals_072 = metadata_linked[
        metadata_linked["machine_name"] == "ETHOSCOPE_072"
    ].head(1)

    # Test velocity thresholds from 0.1 to 5.0
    velocity_thresholds = [0.1, 0.2, 0.5, 0.7, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]

    results = []

    print("=== Testing Velocity Thresholds ===")
    print("Format: Machine | FPS | Velocity Threshold | Sleep % | Movement %")
    print("-" * 70)

    for animals, machine_name, fps in [
        (animals_018, "ETHOSCOPE_018", 4.05),
        (animals_072, "ETHOSCOPE_072", 3.56),
    ]:
        print(f"\n{machine_name} (FPS: {fps:.2f}):")

        for vel_threshold in velocity_thresholds:
            try:
                # Custom motion detector with specific velocity threshold
                def custom_motion_detector(
                    data,
                    time_window_length,
                    masking_duration=6,
                    velocity_correction_coef=3e-3,
                ):
                    from ethoscopy.analyse import max_velocity_detector

                    return max_velocity_detector(
                        data,
                        time_window_length=time_window_length,
                        velocity_threshold=vel_threshold,
                        walk_threshold=vel_threshold + 1.5,
                        velocity_correction_coef=velocity_correction_coef,
                        masking_duration=masking_duration,
                    )

                # Custom sleep annotation function using our motion detector
                def custom_sleep_annotation(data):
                    return sleep_annotation(
                        data,
                        time_window_length=10,
                        motion_detector_function=custom_motion_detector,
                        velocity_correction_coef=3e-3,
                    )

                # Load data with custom parameters
                data = load_ethoscope(animals, FUN=custom_sleep_annotation)

                if data is not None and len(data) > 0:
                    sleep_pct = data["asleep"].mean() * 100
                    moving_pct = data["moving"].mean() * 100

                    print(
                        f"  Threshold {vel_threshold:4.1f}: Sleep {sleep_pct:5.1f}% | Movement {moving_pct:5.1f}%"
                    )

                    results.append(
                        {
                            "machine": machine_name,
                            "fps": fps,
                            "velocity_threshold": vel_threshold,
                            "sleep_percentage": sleep_pct,
                            "movement_percentage": moving_pct,
                        }
                    )
                else:
                    print(f"  Threshold {vel_threshold:4.1f}: Failed to load data")

            except Exception as e:
                print(f"  Threshold {vel_threshold:4.1f}: Error - {e}")

    # Convert to DataFrame for analysis
    results_df = pd.DataFrame(results)

    # Save results
    results_df.to_csv("velocity_threshold_test_results.csv", index=False)
    print(f"\n=== Results saved to velocity_threshold_test_results.csv ===")

    # Find optimal thresholds (targeting ~20-40% sleep)
    print(f"\n=== Optimal Threshold Recommendations ===")
    for machine in ["ETHOSCOPE_018", "ETHOSCOPE_072"]:
        machine_results = results_df[results_df["machine"] == machine]

        # Find threshold that gives sleep percentage closest to 30% (typical target)
        if len(machine_results) > 0:
            target_sleep = 30.0
            machine_results["sleep_diff"] = abs(
                machine_results["sleep_percentage"] - target_sleep
            )
            optimal = machine_results.loc[machine_results["sleep_diff"].idxmin()]

            print(f"{machine}:")
            print(f"  Recommended velocity_threshold: {optimal['velocity_threshold']}")
            print(f"  Expected sleep: {optimal['sleep_percentage']:.1f}%")
            print(f"  Expected movement: {optimal['movement_percentage']:.1f}%")

    return results_df


if __name__ == "__main__":
    results = test_velocity_thresholds()
