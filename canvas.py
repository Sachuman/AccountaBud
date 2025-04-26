from dotenv import load_dotenv
import requests
import os
import json

load_dotenv()  # Load environment variables from .env file

API_URL = "https://canvas.eee.uci.edu/api/v1"
TARGET_GRADE_PERCENTAGE = 93.0

API_TOKEN = os.getenv("CANVAS_API_KEY")

if not API_TOKEN:
    print(
        "Error: CANVAS_API_KEY environment variable not set."
    )
    print(
        "Please set the environment variable before running the script."
    )
    exit(1)  # Exit if the token is not found

headers = {"Authorization": f"Bearer {API_TOKEN}"}

# --- Helper Functions ---


def make_paginated_request(url, params=None, output_lines=None):
    """
    Makes requests to a Canvas API endpoint, handling pagination.
    Returns a list of all items retrieved. Appends errors to output_lines.
    """
    results = []
    next_url = url
    while next_url:
        try:
            response = requests.get(next_url, headers=headers, params=params)
            # Clear params after the first request, as the next_url includes them
            params = None
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                warning_msg = f"Warning: Received dict instead of list from {next_url}"
                print(warning_msg)  # Keep console warning for this case
                if output_lines is not None:
                    output_lines.append(warning_msg)
                return [data]  # Return the dict wrapped in a list
            results.extend(data)

            # Check for 'next' link in the Link header
            next_url = None
            if "Link" in response.headers:
                links = requests.utils.parse_header_links(
                    response.headers["Link"]
                )
                for link in links:
                    if link.get("rel") == "next":
                        next_url = link.get("url")
                        break
        except requests.exceptions.RequestException as e:
            error_msg = f"Error during paginated request to {url}: {e}"
            print(error_msg)  # Keep console error
            if output_lines is not None:
                output_lines.append(error_msg)
            if response is not None:
                error_details = f"Response status: {response.status_code}\nResponse text: {response.text[:500]}..."
                print(error_details)  # Keep console error
                if output_lines is not None:
                    output_lines.append(error_details)
            return None  # Indicate failure
        except json.JSONDecodeError as e:
            error_msg = f"Error decoding JSON from {url}: {e}"
            print(error_msg)  # Keep console error
            if output_lines is not None:
                output_lines.append(error_msg)
            if response is not None:
                error_details = f"Response text: {response.text[:500]}..."
                print(error_details)  # Keep console error
                if output_lines is not None:
                    output_lines.append(error_details)
            return None

    return results

# --- API Functions ---


def get_user_info(output_lines):
    """Fetches user information from Canvas and appends it to output_lines."""
    output_lines.append("\n--- Fetching User Info ---")
    endpoint = f"{API_URL}/users/self"
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        user_data = response.json()
        output_lines.append(json.dumps(user_data, indent=2)
                            )  # Append pretty print
        return user_data
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching user info: {e}"
        print(error_msg)  # Keep console error
        output_lines.append(error_msg)
        return None


def get_my_courses(output_lines):
    """Fetches active courses and appends info to output_lines."""
    output_lines.append("\n--- Fetching Courses ---")
    endpoint = f"{API_URL}/courses"
    params = {"enrollment_state": "active", "per_page": 50}
    courses = make_paginated_request(
        endpoint, params=params, output_lines=output_lines)
    if courses:
        output_lines.append(f"Found {len(courses)} active courses.")
        # Example: Append names and IDs
        for course in courses:
            output_lines.append(
                f"- ID: {course.get('id')}, Name: {course.get('name')}")
    else:
        output_lines.append("Could not retrieve courses.")
    return courses


def get_assignments(course_id, course_name, output_lines):
    """Fetches assignments and appends info to output_lines."""
    output_lines.append(
        f"\n--- Fetching Assignments for Course: {course_name} (ID: {course_id}) ---")
    endpoint = f"{API_URL}/courses/{course_id}/assignments"
    params = {"per_page": 100}  # Get more per page if needed
    assignments = make_paginated_request(
        endpoint, params=params, output_lines=output_lines)
    if assignments:
        output_lines.append(f"Found {len(assignments)} assignments.")
    else:
        output_lines.append("Could not retrieve assignments.")
    return assignments


def get_my_submissions(course_id, course_name, output_lines):
    """Fetches submissions and appends info to output_lines."""
    output_lines.append(
        f"\n--- Fetching Your Submissions for Course: {course_name} (ID: {course_id}) ---")
    endpoint = f"{API_URL}/courses/{course_id}/students/submissions"
    params = {"student_ids[]": "self",
              "include[]": "assignment", "per_page": 100}
    submissions = make_paginated_request(
        endpoint, params=params, output_lines=output_lines)
    if submissions:
        output_lines.append(f"Found {len(submissions)} submissions for you.")
    else:
        output_lines.append("Could not retrieve your submissions.")
    return submissions

# --- Calculation Function ---


def calculate_needed_score(assignments, submissions, target_percentage, output_lines):
    """
    Estimates the percentage needed on remaining assignments. Appends results to output_lines.
    """
    output_lines.append(
        f"\n--- Calculating Score Needed for {target_percentage}% (Simplified) ---")
    if assignments is None or submissions is None:
        output_lines.append(
            "Cannot calculate score: Missing assignments or submissions data.")
        return

    total_points_possible = 0.0
    total_score_earned = 0.0
    remaining_points_possible = 0.0
    graded_points_possible = 0.0  # Track points for graded items

    submissions_dict = {sub.get("assignment_id"): sub for sub in submissions}

    for assign in assignments:
        # Consider only published assignments with positive points possible
        # Skip assignments in 'Never Drop' groups if needed (more complex logic)
        if assign.get("published") and assign.get("points_possible") is not None and assign.get("points_possible") > 0:
            points = float(assign["points_possible"])
            assignment_id = assign.get("id")
            submission = submissions_dict.get(assignment_id)

            # Always add to total possible points for the course
            total_points_possible += points

            # Check submission status to categorize points
            # Ensure score is not None before attempting float conversion
            if submission and submission.get("score") is not None and \
               (submission.get("workflow_state") == "graded" or submission.get("graded_at")):
                # Graded submission
                try:
                    total_score_earned += float(submission["score"])
                    graded_points_possible += points
                except (ValueError, TypeError):
                    warning_msg = f"Warning: Could not convert score '{submission['score']}' to float for assignment ID {assignment_id}. Skipping."
                    print(warning_msg)  # Keep console warning
                    output_lines.append(warning_msg)
                    remaining_points_possible += points  # Treat as ungraded if score is invalid
            else:
                # Ungraded, not submitted, submitted but score is null, or score conversion failed
                remaining_points_possible += points

    if total_points_possible == 0:
        output_lines.append(
            "Cannot calculate score: No assignments with points found or processed.")
        return

    current_percentage = (total_score_earned / graded_points_possible) * \
        100 if graded_points_possible > 0 else 0.0
    target_total_score = (target_percentage / 100.0) * total_points_possible
    points_needed = target_total_score - total_score_earned

    # --- Append Results ---
    output_lines.append(
        f"Total Points Possible (Course): {total_points_possible:.2f}")
    output_lines.append(
        f"Total Score Earned (Graded):   {total_score_earned:.2f}")
    output_lines.append(
        f"Points Possible (Graded):      {graded_points_possible:.2f}")
    output_lines.append(
        f"Current Percentage (Graded):   {current_percentage:.2f}%")
    output_lines.append(
        f"Points Possible (Remaining):   {remaining_points_possible:.2f}")
    output_lines.append(
        f"Target Score for {target_percentage:.1f}%:      {target_total_score:.2f} points")
    output_lines.append(
        f"Points Still Needed:           {max(0, points_needed):.2f}")

    # --- Final Conclusion ---
    if remaining_points_possible <= 0:
        if total_score_earned >= target_total_score:
            points_over_target = total_score_earned - target_total_score
            output_lines.append(
                f"\n>>> Conclusion: Target already achieved or exceeded! (All points graded)")
            output_lines.append(
                f"   You are {points_over_target:.2f} points above the score needed for {target_percentage:.1f}%.")
        else:
            output_lines.append(
                f"\n>>> Conclusion: Target of {target_percentage:.1f}% not met. (All points graded)")
            output_lines.append(
                f"   You were {abs(points_needed):.2f} points short.")
    elif points_needed <= 0:
        points_over_target = -points_needed
        output_lines.append(
            f"\n>>> Conclusion: Target of {target_percentage:.1f}% already achieved or exceeded!")
        output_lines.append(
            f"   You are currently {points_over_target:.2f} points above the total score needed.")
        output_lines.append(
            f"   You need 0 points from the remaining {remaining_points_possible:.2f} points to maintain this target.")
    else:
        percentage_needed_on_remaining = (
            points_needed / remaining_points_possible) * 100.0
        output_lines.append(
            f"\n>>> Conclusion: To achieve {target_percentage:.1f}%, you need an average of {percentage_needed_on_remaining:.2f}%")
        output_lines.append(
            f"   on the remaining {remaining_points_possible:.2f} points possible ({points_needed:.2f} points needed).")
        if percentage_needed_on_remaining > 100:
            output_lines.append(
                "   (Note: Requires >100% average, check for extra credit possibilities)")
        if percentage_needed_on_remaining > 110:
            output_lines.append(
                "   (Warning: Target may be difficult/unrealistic without significant extra credit)")

# --- Main Execution ---


def run_canvas_analysis():
    """Runs the full analysis and returns the output as a single string."""
    output_lines = []  # Initialize list to store output lines

    # Check API Token (keep console print for immediate feedback)
    if not API_TOKEN:
        print("Error: CANVAS_API_KEY environment variable not set.")
        print("Please set the environment variable before running the script.")
        output_lines.append(
            "Error: CANVAS_API_KEY environment variable not set.")
        return "\n".join(output_lines)  # Return early with error

    user_info = get_user_info(output_lines)
    courses = get_my_courses(output_lines)

    if courses:
        for course in courses:
            COURSE_ID_TO_CHECK = course.get("id")
            COURSE_NAME_TO_CHECK = course.get(
                "name", "Unnamed Course")  # Default name
            if COURSE_ID_TO_CHECK:
                assignments = get_assignments(
                    COURSE_ID_TO_CHECK, COURSE_NAME_TO_CHECK, output_lines)
                submissions = get_my_submissions(
                    COURSE_ID_TO_CHECK, COURSE_NAME_TO_CHECK, output_lines)
                if assignments is not None and submissions is not None:
                    calculate_needed_score(
                        assignments, submissions, TARGET_GRADE_PERCENTAGE, output_lines)
                else:
                    output_lines.append(
                        f"\nSkipping grade calculation due to errors fetching assignments or submissions for course {COURSE_NAME_TO_CHECK} (ID: {COURSE_ID_TO_CHECK}).")
            else:
                # This case should be less likely if get_my_courses worked, but good to handle
                output_lines.append(
                    f"\nSkipping course '{COURSE_NAME_TO_CHECK}' because it has no ID.")
    else:
        output_lines.append("\nCannot proceed without course list.")

    # Join all collected lines into a single string
    return "\n".join(output_lines)


if __name__ == "__main__":
    final_output_string = run_canvas_analysis()
    print(final_output_string)  # Print the final combined string
