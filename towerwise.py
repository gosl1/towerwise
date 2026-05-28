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
    # Initialize your data structures as proposed
    U = set(uncovered_barangays)  # Copying to avoid mutating the original input
    candidates = list(candidate_sites)
    approved_sites = []
    
    # Track metrics for the final "Unapproved Site Report" feature
    rejected_sites_report = []

    # Main Greedy Loop: Repeat until all barangays are covered
    iteration = 1
    while U:
        print(f"\n--- Iteration {iteration} ---")
        print(f"Remaining uncovered barangays: {len(U)}")
        
        best_site = None
        best_ratio = float('inf')
        best_new_coverage = set()

        # Step 1: Evaluate the local choice for every remaining candidate site
        for site_id, covered_bgrys, cost in candidates:
            # Compute set intersection: new_coverage = |t.barangays ∩ U|
            new_coverage = covered_bgrys.intersection(U)
            
            # Skip if this site offers absolutely no new coverage
            if len(new_coverage) == 0:
                continue
            
            # Compute cost-effectiveness ratio: cost / size of new coverage
            ratio = cost / len(new_coverage)
            print(f"  Site {site_id}: ₱{cost:,.2f} / {len(new_coverage)} new barangays = ₱{ratio:,.2f} per barangay")
            
            # Local Selection Choice: Find the argmin ratio
            if ratio < best_ratio:
                best_ratio = ratio
                best_site = (site_id, covered_bgrys, cost)
                best_new_coverage = new_coverage

        # Step 2: Safety check for unachievable configurations
        # If U is not empty but no site provides new coverage, the problem is unsolvable
        if best_site is None:
            print("\n[WARNING]: Total coverage impossible with current candidate sites!")
            print(f"Uncovered barangays: {U}")
            break

        # Step 3: State Update
        site_id, covered_bgrys, cost = best_site
        
        print(f"\n✓ Selected Site {site_id}: ₱{cost:,.2f} covering {len(best_new_coverage)} new barangay(s)")
        
        # Record the breakdown data before updating U (crucial for your UI report)
        approved_sites.append({
            "site_id": site_id,
            "cost": cost,
            "total_covered": list(covered_bgrys),
            "unique_contribution": list(best_new_coverage)
        })
        
        # Remove newly covered barangays from Set U
        U.difference_update(best_new_coverage)
        
        # Remove the chosen site from the pool of remaining candidates
        candidates = [c for c in candidates if c[0] != site_id]
        
        iteration += 1

    # Step 4: Populate the Unapproved Site Report for the remaining rejected sites
    for site_id, covered_bgrys, cost in candidates:
        rejected_sites_report.append({
            "site_id": site_id,
            "cost": cost,
            "covered_barangays": list(covered_bgrys),
            "reason": "Redundant coverage (All target barangays already served by selected sites)"
        })

    return approved_sites, rejected_sites_report


def display_results(approved_sites, rejected_sites_report, total_barangays):
    """
    Display the optimization results in a formatted way.
    """
    print("\n" + "="*70)
    print("TOWERWISE OPTIMIZATION RESULTS")
    print("="*70)
    
    # Summary
    total_cost = sum(site["cost"] for site in approved_sites)
    total_sites = len(approved_sites)
    
    # Calculate unique coverage
    all_covered = set()
    for site in approved_sites:
        all_covered.update(site["unique_contribution"])
    
    print(f"\n📊 SUMMARY:")
    print(f"  • Total approved sites: {total_sites}")
    print(f"  • Total cost: ₱{total_cost:,.2f}")
    print(f"  • Barangays covered: {len(all_covered)}/{total_barangays}")
    
    # Per-site breakdown
    print(f"\n📡 APPROVED SITES (in selection order):")
    print("-"*70)
    for i, site in enumerate(approved_sites, 1):
        print(f"\n  Site {i}: {site['site_id']}")
        print(f"    Cost: ₱{site['cost']:,.2f}")
        print(f"    Total barangays covered: {len(site['total_covered'])}")
        print(f"    Uniquely contributes to: {', '.join(site['unique_contribution'])}")
        print(f"    Full coverage: {', '.join(site['total_covered'])}")
    
    # Unapproved sites report
    if rejected_sites_report:
        print(f"\n🚫 UNAPPROVED SITES:")
        print("-"*70)
        for site in rejected_sites_report:
            print(f"\n  Site: {site['site_id']}")
            print(f"    Cost: ₱{site['cost']:,.2f}")
            print(f"    Would cover: {', '.join(site['covered_barangays'])}")
            print(f"    Reason: {site['reason']}")
    
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
    
    # Validate each candidate site
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
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        validate_input_data(data)
        
        # Extract barangays
        barangays = data["barangays"]
        
        # Extract candidate sites and convert to tuple format
        candidate_sites = []
        for site in data["candidate_sites"]:
            candidate_sites.append((
                site["id"],
                frozenset(site["covered_barangays"]),
                float(site["cost"])
            ))
        
        return barangays, candidate_sites
    
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{filepath}'.")
        print(f"Details: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: Invalid data structure in '{filepath}'.")
        print(f"Details: {e}")
        sys.exit(1)


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
    
    try:
        with open(output_filepath, 'w', encoding='utf-8') as file:
            json.dump(results, file, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to: {output_filepath}")
    except Exception as e:
        print(f"Warning: Could not save results to file. Error: {e}")


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
    
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(sample_data, file, indent=2, ensure_ascii=False)
        print(f"✓ Sample JSON file created at: {filepath}")
    except Exception as e:
        print(f"Error creating sample file: {e}")


def main():
    """
    Main function to run the TowerWise optimizer.
    """
    print("="*70)
    print("TOWERWISE: Cell Tower Placement Optimizer")
    print("Weighted Set Cover - Greedy Approximation Algorithm")
    print("="*70)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        print(f"\n📂 Loading configuration from: {json_file}")
        barangays, candidate_sites = load_from_json(json_file)
    else:
        # Interactive mode - ask for file path
        print("\nNo JSON file provided.")
        print("Usage: python towerwise.py <config_file.json>")
        print("\nOptions:")
        print("  1. Enter path to JSON configuration file")
        print("  2. Create a sample JSON file to use as template")
        
        choice = input("\nChoose option (1 or 2): ").strip()
        
        if choice == "2":
            sample_file = input("Enter filename for sample (e.g., sample_config.json): ").strip()
            if not sample_file:
                sample_file = "towerwise_sample.json"
            create_sample_json(sample_file)
            print(f"\nEdit '{sample_file}' with your data, then run:")
            print(f"python towerwise.py {sample_file}")
            return
        else:
            json_file = input("Enter path to JSON configuration file: ").strip()
            if not json_file:
                print("Error: No file specified.")
                return
            barangays, candidate_sites = load_from_json(json_file)
    
    # Display loaded data summary
    print(f"\n✓ Loaded {len(barangays)} barangays:")
    for bgry in barangays:
        print(f"  • {bgry}")
    
    print(f"\n✓ Loaded {len(candidate_sites)} candidate sites:")
    for site_id, covered, cost in candidate_sites:
        print(f"  • {site_id}: ₱{cost:,.2f} - covers {len(covered)} barangay(s)")
    
    # Run optimizer
    print("\n" + "="*70)
    print("RUNNING GREEDY OPTIMIZATION...")
    print("="*70)
    
    approved_sites, rejected_sites = run_towerwise_optimizer(barangays, candidate_sites)
    
    # Display results
    display_results(approved_sites, rejected_sites, len(barangays))
    
    # Ask to save results
    save_choice = input("\n💾 Save results to JSON file? (y/n): ").strip().lower()
    if save_choice == 'y':
        output_file = input("Enter output filename (e.g., results.json): ").strip()
        if not output_file:
            output_file = "towerwise_results.json"
        save_results_to_json(approved_sites, rejected_sites, output_file)
    
    print("\n✓ TowerWise optimization complete!")


if __name__ == "__main__":
    main()