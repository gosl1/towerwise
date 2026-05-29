import json
import os
import sys
from pathlib import Path


def run_towerwise_optimizer(uncovered_barangays, candidate_sites):
    """
    Executes the Greedy Approximation for Weighted Set Cover from scratch.

    Inputs:
        uncovered_barangays (set): Set U of all target barangays.
        candidate_sites (list): List of tuples (site_id, covered_frozenset, cost).

    Returns:
        approved_sites (list): List of selected site data for the final recommendation.
        unapproved_sites (list): List of rejected sites with reasons for transparency.
    """
    U = set(uncovered_barangays)
    candidates = list(candidate_sites)
    approved_sites = []
    rejected_sites_report = []

    while U:
        best_site = None
        best_ratio = float('inf')
        best_new_coverage = set()

        for site_id, covered_bgrys, cost in candidates:
            new_coverage = covered_bgrys.intersection(U)

            if len(new_coverage) == 0:
                continue

            ratio = cost / len(new_coverage)

            if ((ratio < best_ratio) or
            (ratio == best_ratio and len(new_coverage) > len(best_new_coverage)) or
            (ratio == best_ratio and len(new_coverage) == len(best_new_coverage) and cost < best_site[2])):
                best_ratio = ratio
                best_site = (site_id, covered_bgrys, cost)
                best_new_coverage = new_coverage

        if best_site is None:
            print("\n[WARNING]: Total coverage impossible with current candidate sites!")
            print(f"Uncovered barangays: {U}")
            break

        site_id, covered_bgrys, cost = best_site

        approved_sites.append({
            "site_id": site_id,
            "cost": cost,
            "total_covered": list(covered_bgrys),
            "unique_contribution": list(best_new_coverage)
        })

        U.difference_update(best_new_coverage)
        candidates = [c for c in candidates if c[0] != site_id]

    for site_id, covered_bgrys, cost in candidates:
        rejected_sites_report.append({
            "site_id": site_id,
            "cost": cost,
            "covered_barangays": list(covered_bgrys),
        })

    return approved_sites, rejected_sites_report


def display_results(approved_sites, rejected_sites_report, total_barangays):
    """
    Display the optimization results in a formatted way.
    """
    print("\n" + "="*70)
    print("TOWERWISE OPTIMIZATION RESULTS")
    print("="*70)

    total_cost = sum(site["cost"] for site in approved_sites)
    total_sites = len(approved_sites)

    all_covered = set()
    for site in approved_sites:
        all_covered.update(site["unique_contribution"])

    print("\nSummary:")
    print(f"  - Total approved sites: {total_sites}")
    print(f"  - Total cost: ₱{total_cost:,.2f}")
    print(f"  - Barangays covered: {len(all_covered)}/{total_barangays}")

    print(f"\nApproved sites (in selection order):")
    print("-"*70)
    for i, site in enumerate(approved_sites, 1):
        print(f"\n  Site {i}: {site['site_id']}")
        print(f"    Cost: ₱{site['cost']:,.2f}")
        print(f"    Total barangays covered: {len(site['total_covered'])}")
        print(f"    Uniquely contributes to: {', '.join(site['unique_contribution'])}")
        print(f"    Full coverage: {', '.join(site['total_covered'])}")

    if rejected_sites_report:
        print(f"\nUnapproved sites:")
        print("-"*70)
        print(f"\nReason: Redundancy, other sites cost less and offer a greater or equal coverage")
        for site in rejected_sites_report:
            print(f"\n  Site: {site['site_id']}")
            print(f"    Cost: ₱{site['cost']:,.2f}")
            print(f"    Would cover: {', '.join(site['covered_barangays'])}")

    print("\n" + "="*70)


def validate_input_data(data):
    """
    Validate the JSON input structure.
    """
    required_fields = ["barangays", "candidate_sites"]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: '{field}'")

    if not isinstance(data["barangays"], list):
        raise ValueError("'barangays' must be a list")

    if not isinstance(data["candidate_sites"], list):
        raise ValueError("'candidate_sites' must be a list")

    if len(data["barangays"]) == 0:
        raise ValueError("At least one barangay must be specified")

    if len(data["candidate_sites"]) == 0:
        raise ValueError("At least one candidate site must be specified")

    for i, site in enumerate(data["candidate_sites"]):
        if "id" not in site:
            raise ValueError(f"Candidate site {i} missing 'id' field")
        if "covered_barangays" not in site:
            raise ValueError(f"Candidate site {site.get('id', i)} missing 'covered_barangays' field")
        if "cost" not in site:
            raise ValueError(f"Candidate site {site.get('id', i)} missing 'cost' field")

        if not isinstance(site["covered_barangays"], list):
            raise ValueError(f"Candidate site {site['id']}: 'covered_barangays' must be a list")

        if not isinstance(site["cost"], (int, float)) or site["cost"] <= 0:
            raise ValueError(f"Candidate site {site['id']}: 'cost' must be a positive number")

    return True


def load_from_json(filepath):
    """
    Load the problem configuration from a JSON file.
    Raises exceptions instead of calling sys.exit() so callers can handle errors.
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)

    validate_input_data(data)

    barangays = data["barangays"]

    candidate_sites = []
    for site in data["candidate_sites"]:
        candidate_sites.append((
            site["id"],
            frozenset(site["covered_barangays"]),
            float(site["cost"])
        ))

    return barangays, candidate_sites


def save_results_to_json(approved_sites, rejected_sites, output_filepath):
    """
    Save the optimization results to a JSON file.
    """
    results = {
        "approved_sites": approved_sites,
        "rejected_sites": rejected_sites,
        "total_cost": sum(site["cost"] for site in approved_sites),
        "total_sites": len(approved_sites)
    }

    with open(output_filepath, 'w', encoding='utf-8') as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    print(f"Results saved to: {output_filepath}")


def create_sample_json(filepath):
    """
    Create a sample JSON configuration file.
    """
    sample_data = {
        "barangays": ["Barangay 1", "Barangay 2", "Barangay 3", "Barangay 4", "Barangay 5", "Barangay 6"],
        "candidate_sites": [
            {
                "id": "Site A",
                "covered_barangays": ["Barangay 1", "Barangay 2", "Barangay 3"],
                "cost": 800000
            },
            {
                "id": "Site B",
                "covered_barangays": ["Barangay 2", "Barangay 3", "Barangay 4", "Barangay 5"],
                "cost": 600000
            },
            {
                "id": "Site C",
                "covered_barangays": ["Barangay 4", "Barangay 5", "Barangay 6"],
                "cost": 500000
            },
            {
                "id": "Site D",
                "covered_barangays": ["Barangay 1", "Barangay 6"],
                "cost": 400000
            }
        ]
    }

    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(sample_data, file, indent=2, ensure_ascii=False)

    print(f"Sample config created at: {filepath}")


def list_data_files():
    """
    List available .json files in the data/ folder.
    Returns a list of filenames, or an empty list if the folder doesn't exist.
    """
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    return sorted(f.name for f in data_dir.glob("*.json"))


def prompt_for_filename():
    """
    Show available files in data/ and prompt until a valid filename is entered.
    """
    available = list_data_files()

    if available:
        print("\nAvailable configs in data/:")
        for f in available:
            print(f"  - {f}")
    else:
        print("\n(No .json files found in data/ yet.)")

    while True:
        filename = input("\nEnter filename (e.g., config.json): ").strip()
        if filename:
            return filename
        print("Filename cannot be empty. Please try again.")


def main():
    """
    Main function to run the TowerWise optimizer.
    """
    print("="*70)
    print("TOWERWISE: Cell Tower Placement Optimizer")
    print("Weighted Set Cover - Greedy Approximation Algorithm")
    print("="*70)

    # --- Load config ---
    if len(sys.argv) > 1:
        # CLI mode: accept a full path or just a filename (checked in data/ if not found directly)
        arg = sys.argv[1]
        filepath = Path(arg) if Path(arg).exists() else Path("data") / arg
        print(f"\nLoading configuration from: {filepath}")
        try:
            barangays, candidate_sites = load_from_json(filepath)
        except FileNotFoundError:
            print(f"Error: '{filepath}' not found.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in '{filepath}'.\nDetails: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: Invalid data in '{filepath}'.\nDetails: {e}")
            sys.exit(1)
    else:
        # Interactive mode
        print("\nOptions:")
        print("  1. Run optimizer with a config from data/")
        print("  2. Create a sample config in data/")

        while True:
            choice = input("\nChoose option (1 or 2): ").strip()
            if choice in ("1", "2"):
                break
            print("Please enter 1 or 2.")

        if choice == "2":
            available = list_data_files()
            if available:
                print("\nExisting configs in data/:")
                for f in available:
                    print(f"  - {f}")

            while True:
                sample_file = input("\nEnter filename for sample (default: towerwise_sample.json): ").strip()
                if not sample_file:
                    sample_file = "towerwise_sample.json"
                if not sample_file.endswith(".json"):
                    sample_file += ".json"
                break

            os.makedirs("data", exist_ok=True)
            dest = os.path.join("data", sample_file)
            try:
                create_sample_json(dest)
                print(f"\nEdit '{dest}' with your data, then run:")
                print(f"  python towerwise.py {sample_file}")
            except Exception as e:
                print(f"Error creating sample file: {e}")
            return

        else:
            filename = prompt_for_filename()
            filepath = Path("data") / filename
            try:
                barangays, candidate_sites = load_from_json(filepath)
            except FileNotFoundError:
                print(f"\nError: '{filepath}' not found. Check the filename and try again.")
                sys.exit(1)
            except json.JSONDecodeError as e:
                print(f"\nError: Invalid JSON in '{filepath}'.\nDetails: {e}")
                sys.exit(1)
            except ValueError as e:
                print(f"\nError: Invalid data in '{filepath}'.\nDetails: {e}")
                sys.exit(1)

    # --- Run optimizer ---
    print(f"\nLoaded {len(barangays)} barangay(s) and {len(candidate_sites)} candidate site(s).")
    print("\n" + "="*70)
    print("RUNNING GREEDY OPTIMIZATION...")
    print("="*70)

    approved_sites, rejected_sites = run_towerwise_optimizer(barangays, candidate_sites)

    display_results(approved_sites, rejected_sites, len(barangays))

    # --- Auto-save results ---
    input_stem = Path(filepath).stem if 'filepath' in dir() else "results"
    default_output = f"results_{input_stem}.json"

    save_choice = input(f"\nSave results to JSON? (default: {default_output}) [y/n]: ").strip().lower()
    if save_choice == 'y':
        custom = input(f"Custom filename? (press Enter to use '{default_output}'): ").strip()
        output_file = custom if custom else default_output
        if not output_file.endswith(".json"):
            output_file += ".json"
        try:
            save_results_to_json(approved_sites, rejected_sites, output_file)
        except Exception as e:
            print(f"Warning: Could not save results. Error: {e}")

    print("\nTowerWise optimization complete!")


if __name__ == "__main__":
    main()