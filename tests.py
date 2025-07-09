#!/usr/bin/env python3
"""
🎯 SURVIVABLE TEST HARNESS

External testing framework that survives internal disasters.
Now enhanced with beautiful MCP tools playground for regression hunting.

TESTING MODES:
- Normal Testing: DEV, PROD (traditional testing)
- Regression Hunting: -N days back with binary search

PROGRESSIVE INTELLIGENCE HIERARCHY:
- Level 1: Direct tool imports for super-brain models
- Level 2: Simple execute_tool() calls for smart models  
- Level 3: Command pattern parsing for local LLMs
"""
import argparse
import sys
import time
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta

# Traditional testing imports
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# NEW: MCP Tools Playground imports
try:
    from tools import RegressionHunter, execute_tool, parse_command, get_api_help
    from tools.commit_explorer import CommitExplorer, explore_commit, restore_commit
    from tools.branch_manager import BranchManager, create_bughunt_branch, cleanup_branches
    MCP_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MCP Tools not available: {e}")
    MCP_TOOLS_AVAILABLE = False

class TestResults:
    """Track test results across normal and regression testing modes."""
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        
    def add_result(self, test_name: str, success: bool, details: dict = None):
        self.results[test_name] = {
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
    def get_summary(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r['success'])
        failed = total - passed
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'success_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            'duration': f"{time.time() - self.start_time:.2f}s",
            'results': self.results
        }

def test_server_health():
    """Test if the Pipulate server is responding."""
    try:
        response = requests.get("http://localhost:5001", timeout=10)
        return response.status_code == 200
    except:
        return False

def test_api_health():
    """Test if key API endpoints are working."""
    try:
        # Test the profiles endpoint
        response = requests.get("http://localhost:5001/profiles", timeout=10)
        return response.status_code == 200
    except:
        return False

def test_profile_system():
    """Test the profile creation system via browser automation."""
    try:
        from selenium.webdriver.chrome.options import Options
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:5001/profiles")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if profile creation form exists
        name_field = driver.find_element(By.NAME, "name")
        
        # Fill form with test data (this tests template processing)
        name_field.send_keys("AI_Test_Run_20250709_012756")
        
        real_name_field = driver.find_element(By.NAME, "real_name")
        real_name_field.send_keys("AI Automated Test")
        
        address_field = driver.find_element(By.NAME, "address")  
        address_field.send_keys("123 Test Street")
        
        code_field = driver.find_element(By.NAME, "code")
        code_field.send_keys("TEST123")
        
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for redirect/response
        time.sleep(2)
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"Profile system test failed: {e}")
        return False

def test_html_workflow_menu():
    """Test HTML workflow menu functionality."""
    try:
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("http://localhost:5001")
        
        # Look for workflow menu elements
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # This test is currently failing - but that's GOOD for regression hunting!
        menu_exists = len(driver.find_elements(By.CLASS_NAME, "workflow-menu")) > 0
        
        driver.quit()
        return menu_exists
        
    except Exception as e:
        print(f"HTML workflow menu test failed: {e}")
        return False

def run_normal_tests(mode: str) -> TestResults:
    """Run traditional DEV/PROD testing."""
    print(f"🧪 Running {mode} tests...")
    results = TestResults()
    
    # Core infrastructure tests
    print("  Testing server health...")
    results.add_result("server_health", test_server_health())
    
    print("  Testing API health...")
    results.add_result("api_health", test_api_health())
    
    print("  Testing profile system...")
    results.add_result("profile_system", test_profile_system())
    
    print("  Testing HTML workflow menu...")
    results.add_result("html_workflow_menu", test_html_workflow_menu())
    
    return results

def white_rabbit_assert_test(commit_hash: str, touch_server: bool = True) -> dict:
    """
    The deterministic White Rabbit assertion test.
    
    Tests for "Welcome to Consoleland" in server logs after:
    1. Git checkout to specific commit (in parent pipulate directory)
    2. Optional touch server.py (for deliberate restart control)
    3. 15-second delay for server restart
    4. Grep for the white rabbit message
    
    Returns:
        dict: {"success": bool, "message": str, "details": dict}
    """
    try:
        print(f"🔍 Testing commit {commit_hash[:7]} for White Rabbit...")
        
        # CRITICAL: Work in sibling pipulate directory where server runs
        pipulate_dir = "../pipulate"
        abs_pipulate_dir = os.path.abspath(pipulate_dir)
        print(f"   📁 Working directory: {abs_pipulate_dir}")
        
        # Step 0: Check current state and handle detached HEAD
        current_commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"], 
            capture_output=True, text=True, cwd=pipulate_dir
        )
        
        if current_commit_result.returncode == 0:
            current_commit = current_commit_result.stdout.strip()
            print(f"   📍 Current commit: {current_commit[:7]}")
            
            # Check if we're in detached HEAD state
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"], 
                capture_output=True, text=True, cwd=pipulate_dir
            )
            if not branch_result.stdout.strip():
                print(f"   ⚠️  WARNING: Starting from detached HEAD state")
        
        # Step 1: Git checkout in pipulate directory
        checkout_cmd = ["git", "checkout", commit_hash]
        print(f"   🔧 Running: git checkout {commit_hash[:7]} in {abs_pipulate_dir}")
        checkout_result = subprocess.run(checkout_cmd, capture_output=True, text=True, cwd=pipulate_dir)
        
        if checkout_result.returncode != 0:
            return {
                "success": False,
                "message": f"Git checkout failed: {checkout_result.stderr.strip()}",
                "details": {
                    "commit": commit_hash, 
                    "step": "checkout",
                    "stdout": checkout_result.stdout.strip(),
                    "stderr": checkout_result.stderr.strip()
                }
            }
        
        # Step 1.5: VERIFY the checkout actually worked
        verify_commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"], 
            capture_output=True, text=True, cwd=pipulate_dir
        )
        
        if verify_commit_result.returncode != 0:
            return {
                "success": False,
                "message": f"Cannot verify current commit: {verify_commit_result.stderr.strip()}",
                "details": {"commit": commit_hash, "step": "verification"}
            }
        
        actual_commit = verify_commit_result.stdout.strip()
        if actual_commit != commit_hash:
            return {
                "success": False,
                "message": f"Checkout verification failed! Expected {commit_hash[:7]}, got {actual_commit[:7]}",
                "details": {
                    "commit": commit_hash, 
                    "step": "verification",
                    "expected": commit_hash,
                    "actual": actual_commit
                }
            }
        
        print(f"   ✅ Checkout verified: Now on {actual_commit[:7]}")
        
        # Step 1.7: Show some file modification times to verify code changed
        server_py_path = os.path.join(pipulate_dir, "server.py")
        if os.path.exists(server_py_path):
            stat_info = os.stat(server_py_path)
            mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%H:%M:%S")
            print(f"   📄 server.py last modified: {mod_time}")
        else:
            print(f"   ⚠️  server.py not found at {server_py_path}")
        
        # Step 2: Optional touch server.py for deliberate restart control
        if touch_server:
            touch_cmd = ["touch", "server.py"]
            subprocess.run(touch_cmd, cwd=pipulate_dir)
            print("   📝 Touched server.py for deliberate restart control")
        
        # Step 3: 15-second delay for server restart
        print("   ⏱️  Waiting 15 seconds for server restart...")
        for i in range(15, 0, -1):
            print(f"      ⏳ {i} seconds remaining...")
            time.sleep(1)
        print("   ✅ Server restart wait complete")
        
        # Step 4: Grep for "Welcome to Consoleland" (case insensitive)
        log_path = os.path.join(pipulate_dir, "logs", "server.log")
        grep_cmd = ["grep", "-i", "welcome to consoleland", log_path]
        grep_result = subprocess.run(grep_cmd, capture_output=True, text=True)
        
        white_rabbit_found = grep_result.returncode == 0
        
        result = {
            "success": white_rabbit_found,
            "message": "🐰 White Rabbit FOUND!" if white_rabbit_found else "❌ White Rabbit MISSING",
            "details": {
                "commit": commit_hash,
                "touch_server": touch_server,
                "log_path": log_path,
                "grep_output": grep_result.stdout.strip() if white_rabbit_found else "",
                "grep_error": grep_result.stderr.strip() if not white_rabbit_found else ""
            }
        }
        
        print(f"   {result['message']}")
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"White Rabbit test failed: {str(e)}",
            "details": {"commit": commit_hash, "error": str(e)}
        }

def get_commits_for_timeframe(days_ago: int) -> list:
    """Get list of commit hashes for binary search within timeframe."""
    try:
        # Get commits from N days ago to now
        since_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        git_cmd = [
            "git", "log", 
            f"--since={since_date}",
            "--format=%H",
            "--reverse"  # Oldest first for binary search
        ]
        
        result = subprocess.run(git_cmd, capture_output=True, text=True, cwd="../pipulate")
        
        if result.returncode != 0:
            print(f"❌ Git log failed: {result.stderr}")
            return []
        
        commits = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        print(f"🎯 Found {len(commits)} commits in the last {days_ago} days")
        return commits
        
    except Exception as e:
        print(f"❌ Error getting commits: {e}")
        return []

def binary_search_white_rabbit(commits: list) -> dict:
    """
    Binary search to find the exact commit where White Rabbit disappeared.
    
    Returns the boundary: last commit WITH rabbit, first commit WITHOUT rabbit.
    """
    if not commits:
        return {"success": False, "error": "No commits to search"}
    
    print(f"🔍 BINARY SEARCH: {len(commits)} commits")
    print(f"   Range: {commits[0][:7]} (oldest) ... {commits[-1][:7]} (newest)")
    
    # Check if we need to expand the search range
    if len(commits) < 10:
        print(f"⚠️  WARNING: Only {len(commits)} commits found. Consider expanding search with -14 or -30 days.")
    
    left = 0
    right = len(commits) - 1
    last_good_commit = None
    first_bad_commit = None
    iteration = 0
    
    # Store test results to avoid retesting
    test_cache = {}
    
    while left <= right:
        iteration += 1
        mid = (left + right) // 2
        commit_hash = commits[mid]
        
        print(f"\n📍 ITERATION {iteration}: Testing commit {mid+1}/{len(commits)}")
        print(f"   Commit: {commit_hash[:7]} (position in timeline)")
        print(f"   Search space: commits {left+1} to {right+1} (remaining: {right-left+1})")
        
        # Check cache first
        if commit_hash in test_cache:
            test_result = test_cache[commit_hash]
            print(f"   📋 Using cached result for {commit_hash[:7]}")
        else:
            # Run the White Rabbit assertion test
            test_result = white_rabbit_assert_test(commit_hash)
            test_cache[commit_hash] = test_result
        
        if test_result["success"]:
            # White Rabbit found - this is a GOOD commit
            last_good_commit = commit_hash
            print(f"   ✅ WHITE RABBIT PRESENT - bug is in NEWER commits (searching forward)")
            print(f"      Next search: commits {mid+2} to {right+1}")
            left = mid + 1
        else:
            # White Rabbit missing - this is a BAD commit  
            first_bad_commit = commit_hash
            print(f"   ❌ WHITE RABBIT MISSING - bug is in OLDER commits (searching backward)")
            print(f"      Next search: commits {left+1} to {mid}")
            right = mid - 1
        
        # Show convergence progress
        remaining = right - left + 1
        if remaining > 0:
            print(f"   🎯 Convergence: {remaining} commits remaining to test")
        else:
            print(f"   🎯 Convergence: Search complete!")
    
    # Determine the boundary
    if last_good_commit and first_bad_commit:
        # Find their positions in the commits list for verification
        good_pos = commits.index(last_good_commit) + 1
        bad_pos = commits.index(first_bad_commit) + 1
        return {
            "success": True,
            "boundary_found": True,
            "last_good_commit": last_good_commit,
            "first_bad_commit": first_bad_commit,
            "iterations": iteration,
            "message": f"🎯 BOUNDARY FOUND! Rabbit disappeared between commit {good_pos} ({last_good_commit[:7]}) and commit {bad_pos} ({first_bad_commit[:7]})"
        }
    elif last_good_commit:
        good_pos = commits.index(last_good_commit) + 1
        return {
            "success": True,
            "boundary_found": False,
            "last_good_commit": last_good_commit,
            "iterations": iteration,
            "message": f"🐰 Rabbit present in all tested commits (last good: commit {good_pos} - {last_good_commit[:7]})"
        }
    elif first_bad_commit:
        bad_pos = commits.index(first_bad_commit) + 1
        return {
            "success": True,
            "boundary_found": False,
            "first_bad_commit": first_bad_commit,
            "iterations": iteration,
            "message": f"❌ Rabbit missing in all tested commits (oldest bad: commit {bad_pos} - {first_bad_commit[:7]}). Try searching further back with -14 or -30 days."
        }
    else:
        return {
            "success": False,
            "iterations": iteration,
            "message": "🤔 No conclusive results from binary search"
        }

def ensure_clean_git_state() -> dict:
    """
    Ensure we're starting from a clean git state, handling detached HEAD.
    
    Returns:
        dict: {"success": bool, "message": str, "original_commit": str}
    """
    try:
        pipulate_dir = "../pipulate"
        
        # Check current commit
        current_commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"], 
            capture_output=True, text=True, cwd=pipulate_dir
        )
        
        if current_commit_result.returncode != 0:
            return {
                "success": False,
                "message": f"Cannot determine current commit: {current_commit_result.stderr.strip()}"
            }
        
        current_commit = current_commit_result.stdout.strip()
        
        # Check if we're on a branch or detached HEAD
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"], 
            capture_output=True, text=True, cwd=pipulate_dir
        )
        
        current_branch = branch_result.stdout.strip()
        
        if current_branch:
            # We're on a branch - this is good
            print(f"🌿 Starting from branch: {current_branch} ({current_commit[:7]})")
            return {
                "success": True,
                "message": f"On branch {current_branch}",
                "original_commit": current_commit,
                "branch": current_branch
            }
        else:
            # We're in detached HEAD - need to fix this
            print(f"⚠️  DETACHED HEAD detected at {current_commit[:7]}")
            print(f"🔧 Switching to main branch for clean regression hunt...")
            
            # Switch to main branch
            checkout_main_result = subprocess.run(
                ["git", "checkout", "main"], 
                capture_output=True, text=True, cwd=pipulate_dir
            )
            
            if checkout_main_result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Cannot switch to main branch: {checkout_main_result.stderr.strip()}"
                }
            
            # Verify we're now on main
            verify_result = subprocess.run(
                ["git", "branch", "--show-current"], 
                capture_output=True, text=True, cwd=pipulate_dir
            )
            
            new_branch = verify_result.stdout.strip()
            
            # Get the new HEAD commit
            new_commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"], 
                capture_output=True, text=True, cwd=pipulate_dir
            )
            new_commit = new_commit_result.stdout.strip()
            
            print(f"✅ Switched to branch: {new_branch} ({new_commit[:7]})")
            
            return {
                "success": True,
                "message": f"Fixed detached HEAD, now on {new_branch}",
                "original_commit": new_commit,
                "branch": new_branch,
                "was_detached": True,
                "detached_commit": current_commit
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error checking git state: {str(e)}"
        }

def run_regression_hunt(days_ago: int, auto_expand: bool = True) -> TestResults:
    """
    Run regression hunting using binary search with White Rabbit assertion.
    
    Args:
        days_ago: Initial number of days to search back
        auto_expand: If True, automatically expand search range if no good commits found
    """
    print(f"🕰️ REGRESSION HUNTING MODE: {days_ago} days back")
    results = TestResults()
    
    # Step 0: Ensure clean git state (handle detached HEAD)
    print(f"🔍 Checking git state...")
    git_state = ensure_clean_git_state()
    
    if not git_state["success"]:
        results.add_result("git_state_check", False, git_state)
        return results
    
    results.add_result("git_state_check", True, git_state)
    original_commit_for_restore = git_state["original_commit"]
    
    original_days = days_ago
    max_expansion = 90  # Don't search more than 90 days back
    
    while days_ago <= max_expansion:
        # Get commits for the timeframe
        commits = get_commits_for_timeframe(days_ago)
        
        if not commits:
            if auto_expand and days_ago < max_expansion:
                days_ago *= 2
                print(f"📅 No commits found, expanding search to {days_ago} days...")
                continue
            else:
                results.add_result("commit_retrieval", False, {"error": f"No commits found in {days_ago} days"})
                return results
        
        results.add_result("commit_retrieval", True, {"commit_count": len(commits), "days_searched": days_ago})
        
        # Run binary search for White Rabbit
        print("\n🎯 STARTING BINARY SEARCH FOR WHITE RABBIT...")
        search_result = binary_search_white_rabbit(commits)
        
        # Check if we found a boundary or just all bad commits
        if (search_result.get("success") and 
            not search_result.get("boundary_found") and 
            search_result.get("first_bad_commit") and 
            not search_result.get("last_good_commit")):
            
            # All commits were bad, try expanding the search
            if auto_expand and days_ago < max_expansion:
                expanded_days = min(days_ago * 2, max_expansion)
                print(f"\n🔍 All {len(commits)} commits show missing White Rabbit.")
                print(f"🚀 AUTO-EXPANDING search from {days_ago} to {expanded_days} days...")
                days_ago = expanded_days
                continue
            else:
                print(f"\n⚠️ Reached maximum search range ({max_expansion} days). Consider manual investigation.")
                break
        else:
            # Found boundary or all good commits - we're done
            break
    
    # Add final search details
    search_result["original_days_requested"] = original_days
    search_result["actual_days_searched"] = days_ago 
    search_result["auto_expanded"] = days_ago > original_days
    
    results.add_result("white_rabbit_binary_search", search_result["success"], search_result)
    
    # Restore to original commit
    try:
        print(f"\n🔙 Restoring to original commit: {original_commit_for_restore[:7]}")
        restore_result = subprocess.run(
            ["git", "checkout", original_commit_for_restore], 
            capture_output=True, text=True, cwd="../pipulate"
        )
        
        if restore_result.returncode == 0:
            print(f"✅ Successfully restored to {original_commit_for_restore[:7]}")
            
            # If we were originally on a branch, show it
            if git_state.get("branch"):
                print(f"   Branch: {git_state['branch']}")
        else:
            print(f"⚠️ Warning: Restore failed: {restore_result.stderr.strip()}")
            
    except Exception as e:
        print(f"⚠️ Warning: Could not restore original commit: {e}")
    
    return results

def run_commit_exploration(commits_ago: int) -> TestResults:
    """Run commit exploration for manual bug hunting."""
    print(f"🔍 COMMIT EXPLORATION: {commits_ago} commits ago")
    results = TestResults()
    
    if not MCP_TOOLS_AVAILABLE:
        results.add_result("mcp_tools_check", False, {"error": "MCP tools not available"})
        return results
    
    results.add_result("mcp_tools_check", True)
    
    # Explore the commit
    explorer = CommitExplorer()
    explore_result = explorer.checkout_commit_by_offset(commits_ago)
    results.add_result("commit_exploration", explore_result.get("success", False), explore_result)
    
    return results

def run_branch_management(action: str, **kwargs) -> TestResults:
    """Run branch management operations."""
    print(f"🌿 BRANCH MANAGEMENT: {action}")
    results = TestResults()
    
    if not MCP_TOOLS_AVAILABLE:
        results.add_result("mcp_tools_check", False, {"error": "MCP tools not available"})
        return results
    
    results.add_result("mcp_tools_check", True)
    
    manager = BranchManager()
    
    if action == "create":
        result = manager.create_bughunt_branch(kwargs.get("description", ""))
    elif action == "list":
        result = manager.list_bughunt_branches()
    elif action == "cleanup":
        result = manager.cleanup_resolved_branches(kwargs.get("force", False))
    else:
        result = {"success": False, "error": f"Unknown action: {action}"}
    
    results.add_result(f"branch_{action}", result.get("success", False), result)
    return results

def main():
    """
    🎯 MAIN ENTRY POINT: Two-Phase Bug Hunting Workflow
    
    Phase 1: Manual exploration with simple numeric interface
    Phase 2: Automated binary search with -N days syntax
    """
    # Pre-process sys.argv to handle flexible -N syntax (e.g., -2, -3, -14, etc.)
    processed_args = []
    i = 0
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        # Check if this is a negative number pattern like -2, -3, -14
        if (arg.startswith('-') and len(arg) > 1 and 
            arg[1:].isdigit() and arg not in ['-0', '-1', '-7', '-30']):
            # Convert -N to --days-ago N
            days_num = arg[1:]  # Remove the minus sign
            processed_args.extend(['--days-ago', days_num])
        else:
            processed_args.append(arg)
        i += 1
    
    # Replace sys.argv temporarily for argparse
    original_argv = sys.argv[:]
    sys.argv = processed_args
    
    parser = argparse.ArgumentParser(
            description="Survivable Test Harness with Two-Phase Bug Hunting",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
🔍 TWO-PHASE BUG HUNTING WORKFLOW:

PHASE 1: Manual Exploration (find rough boundaries)
  python tests.py 100       # Checkout 100 commits ago
  python tests.py 50        # Checkout 50 commits ago  
  python tests.py 10        # Checkout 10 commits ago
  python tests.py restore   # Return to original commit

PHASE 2: Automated Binary Search (precise hunting)
  python tests.py -2        # Binary search 2 days back  
  python tests.py -7        # Binary search 7 days back
  python tests.py -14       # Binary search 14 days back
  python tests.py -30       # Binary search 30 days back
  python tests.py --days-ago 14  # Alternative syntax

Branch Management:
  python tests.py --create-branch "Issue description"
  python tests.py --list-branches
  python tests.py --cleanup-branches
  python tests.py --cleanup-branches --force

Normal Testing:
  python tests.py DEV       # Development environment tests
  python tests.py PROD      # Production environment tests

Help:
  python tests.py --mcp-help     # Show MCP tools documentation

The two-phase workflow: Manual exploration finds rough boundaries,
then automated binary search provides logarithmic precision.
            """
        )
    
    # Positional argument that can be numeric (commits ago) or mode (DEV/PROD/restore)
    parser.add_argument('target', nargs='?', 
                       help='Commits ago (100), mode (DEV/PROD), or restore')
    
    # Phase 2: Automated regression hunting modes
    parser.add_argument('-0', '--today', action='store_true',
                       help='Binary search today\'s commits')
    parser.add_argument('-1', '--yesterday', action='store_true', 
                       help='Binary search yesterday\'s commits')
    parser.add_argument('-7', '--week', action='store_true',
                       help='Binary search past week')
    parser.add_argument('-30', '--month', action='store_true',
                       help='Binary search past month')
    parser.add_argument('--days-ago', type=int, 
                       help='Binary search N days back')
    
    # Branch management
    parser.add_argument('--create-branch', type=str, metavar='DESCRIPTION',
                       help='Create new bug hunt branch with description')
    parser.add_argument('--list-branches', action='store_true',
                       help='List active bug hunt branches')
    parser.add_argument('--cleanup-branches', action='store_true',
                       help='Clean up resolved bug hunt branches')
    parser.add_argument('--force', action='store_true',
                       help='Force cleanup of all bug hunt branches')
    
    # Help and info
    parser.add_argument('--mcp-help', action='store_true',
                       help='Show MCP tools documentation')
    
    args = parser.parse_args()
    
    # Show MCP help
    if args.mcp_help:
        if MCP_TOOLS_AVAILABLE:
            print(get_api_help())
        else:
            print("❌ MCP Tools not available. Install the tools/ directory.")
        return
    
    # Branch management commands
    if args.create_branch:
        results = run_branch_management("create", description=args.create_branch)
    elif args.list_branches:
        results = run_branch_management("list")
    elif args.cleanup_branches:
        results = run_branch_management("cleanup", force=args.force)
    
    # Phase 2: Automated binary search regression hunting
    elif args.today:
        results = run_regression_hunt(0)
    elif args.yesterday:
        results = run_regression_hunt(1)
    elif args.week:
        results = run_regression_hunt(7)
    elif args.month:
        results = run_regression_hunt(30)
    elif args.days_ago is not None:
        results = run_regression_hunt(args.days_ago)
    
    # Phase 1: Manual exploration or normal testing
    elif args.target:
        if args.target == "restore":
            # Special restore command - handles both MCP and manual restore
            if MCP_TOOLS_AVAILABLE:
                explorer = CommitExplorer()
                restore_result = explorer.restore_original_commit()
                print(f"🔙 {restore_result.get('message', 'Restore attempted')}")
                if restore_result.get('success'):
                    print(f"   Commit: {restore_result.get('commit', 'Unknown')}")
                    print(f"   {restore_result.get('note', '')}")
                else:
                    print(f"   Error: {restore_result.get('error', 'Unknown error')}")
            else:
                # Manual restore using git state checking
                print("🔧 Manual restore mode (MCP tools not available)")
                git_state = ensure_clean_git_state()
                if git_state["success"]:
                    if git_state.get("was_detached"):
                        print(f"✅ Fixed detached HEAD: {git_state['message']}")
                        print(f"   Was at: {git_state['detached_commit'][:7]}")
                        print(f"   Now on: {git_state['branch']} ({git_state['original_commit'][:7]})")
                    else:
                        print(f"✅ Git state is clean: {git_state['message']}")
                else:
                    print(f"❌ {git_state['message']}")
            return
        elif args.target in ['DEV', 'PROD']:
            # Normal testing modes
            results = run_normal_tests(args.target)
        elif args.target.isdigit():
            # Phase 1: Manual commit exploration
            commits_ago = int(args.target)
            results = run_commit_exploration(commits_ago)
        else:
            print(f"❌ Unknown target: {args.target}")
            print("   Use a number (commits ago), DEV/PROD (testing), or 'restore'")
            parser.print_help()
            return
    else:
        parser.print_help()
        return
    
    # Print results with special handling for different result types
    summary = results.get_summary()
    
    # Special handling for commit exploration
    if 'commit_exploration' in summary['results']:
        explore_result = summary['results']['commit_exploration']
        if explore_result['success']:
            details = explore_result['details']
            print(f"\n{details.get('checkout_message', '')}")
            print(f"{details.get('commit_details', '')}")
            print(f"{details.get('commit_age', '')}")
            print(f"{details.get('commit_subject', '')}")
            print(f"\n{details.get('server_restart_note', '')}")
            print(f"{details.get('wait_message', '')}")
            print(f"\n{details.get('transition_note', '')}")
            print(f"\n🔙 To return to HEAD: {details.get('restore_command', 'python tests.py restore')}")
        else:
            print(f"\n❌ Commit exploration failed: {details.get('error', 'Unknown error')}")
        return
    
    # Special handling for branch management
    if any(key.startswith('branch_') for key in summary['results']):
        for test_name, result in summary['results'].items():
            if test_name.startswith('branch_'):
                action = test_name.replace('branch_', '')
                details = result.get('details', {})
                
                if result['success']:
                    if action == "create":
                        print(f"\n✅ {details.get('message', 'Branch created')}")
                        print(f"   Branch: {details.get('branch_name', 'Unknown')}")
                        print(f"   Original: {details.get('original_branch', 'Unknown')}")
                    elif action == "list":
                        branches = details.get('branches', [])
                        print(f"\n📋 Bug Hunt Branches ({details.get('total_branches', 0)} total):")
                        for branch in branches:
                            status = "✅ RESOLVED" if branch.get('resolved') else "🔍 ACTIVE"
                            print(f"   {status} {branch['branch_name']}")
                            if branch.get('issue_description'):
                                print(f"      📝 {branch['issue_description']}")
                            print(f"      📅 Created: {branch.get('created_at', 'Unknown')}")
                            print(f"      🧪 Tests: {branch.get('commits_tested', 0)}")
                    elif action == "cleanup":
                        print(f"\n🧹 Cleanup completed:")
                        print(f"   Deleted branches: {details.get('deleted_branches', 0)}")
                        print(f"   War stories extracted: {details.get('war_stories_extracted', 0)}")
                        print(f"   Remaining branches: {details.get('remaining_branches', 0)}")
                else:
                    print(f"\n❌ Branch {action} failed: {details.get('error', 'Unknown error')}")
        return
    
    # Standard results output for normal testing and regression hunting
    print(f"\n🎯 TEST SUMMARY:")
    print(f"   Tests Run: {summary['total_tests']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    print(f"   Success Rate: {summary['success_rate']}")
    print(f"   Duration: {summary['duration']}")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, result in summary['results'].items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"   {status} {test_name}")
        
        # Show additional details for regression hunts
        if 'hunt' in test_name and result.get('details', {}).get('regression_found'):
            details = result['details']
            print(f"      🔍 Investigation: {details.get('investigation_command', 'N/A')}")
    
    # Exit code
    exit_code = 0 if summary['failed'] == 0 else 1
    
    # Restore original sys.argv
    sys.argv = original_argv
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
