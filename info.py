import os
from collections import defaultdict
from datetime import datetime

import requests

BASE_URL = "https://codeforces.com/api/"
API_BASE = os.getenv("NODE_API_URL", "http://localhost:3000")


tags_list_all = [
    "math",
    "greedy",
    "dp",
    "data structures",
    "brute force",
    "constructive algorithms",
    "graphs",
    "sortings",
    "binary search",
    "dfs and similar",
    "trees",
    "strings",
    "number theory",
    "combinatorics",
    "geometry",
    "bitmasks",
    "two pointers",
    "hashing",
]

"""
CODEFORCES
"""


def get_codeforces_problems(tags=None, min_rating=None, max_rating=None, limit=50):
    base_url = f"{BASE_URL}problemset.problems"
    standardized_problems = []
    seen = set()

    tag_batches = tags if tags else [None]

    try:
        for tag in tag_batches:
            params = {}
            if tag:
                params["tags"] = tag

            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                continue

            data = response.json()
            if data.get("status") != "OK":
                continue

            problems = data.get("result", {}).get("problems", [])
            problem_stats = data.get("result", {}).get("problemStatistics", [])

            stats_map = {
                f"{s.get('contestId')}_{s.get('index')}": s for s in problem_stats
            }

            for problem in problems:
                contest_id = problem.get("contestId")
                index = problem.get("index")
                key = (contest_id, index)

                if key in seen:
                    continue

                rating = problem.get("rating")

                if min_rating is not None and (rating is None or rating < min_rating):
                    continue
                if max_rating is not None and (rating is None or rating > max_rating):
                    continue

                if rating:
                    if rating <= 1200:
                        difficulty = "easy"
                    elif rating <= 1900:
                        difficulty = "medium"
                    else:
                        difficulty = "hard"
                else:
                    difficulty = "unknown"

                stat = stats_map.get(f"{contest_id}_{index}", {})
                solved_count = stat.get("solvedCount", 0)

                standardized_problems.append(
                    {
                        "platform": "codeforces",
                        "title": problem.get("name", ""),
                        "contestId": contest_id,
                        "index": index,
                        "difficulty": difficulty,
                        "rating": rating,
                        "tags": problem.get("tags", []),
                        "link": f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
                        "type": problem.get("type", "PROGRAMMING"),
                        "points": problem.get("points"),
                        "solved_count": solved_count,
                        "is_contest": False,
                        "contest_start": None,
                        "contest_end": None,
                    }
                )

                seen.add(key)

                if len(standardized_problems) >= limit:
                    return standardized_problems

        return standardized_problems

    except Exception as e:
        print(f"Exception in get_codeforces_problems: {e}")
        return []


def get_codeforces_contests(upcoming=True):
    url = f"{BASE_URL}contest.list"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            if data.get("status") != "OK":
                print(f"Codeforces API error: {data.get('comment', 'Unknown error')}")
                return []

            contests = data.get("result", [])

            if upcoming:
                filtered_contests = [c for c in contests if c.get("phase") == "BEFORE"]
            else:
                filtered_contests = [
                    c for c in contests if c.get("phase") == "FINISHED"
                ]

            standardized_contests = []
            for contest in filtered_contests[:10]:
                start_time = contest.get("startTimeSeconds")
                duration_seconds = contest.get("durationSeconds", 0)

                standardized_contests.append(
                    {
                        "platform": "codeforces",
                        "title": contest.get("name", ""),
                        "contestId": contest.get("id"),
                        "difficulty": None,
                        "rating": None,
                        "tags": [],
                        "link": f"https://codeforces.com/contest/{contest.get('id')}",
                        "type": contest.get("type", "CF"),
                        "is_contest": True,
                        "contest_start": datetime.fromtimestamp(start_time).isoformat()
                        if start_time
                        else None,
                        "contest_end": datetime.fromtimestamp(
                            start_time + duration_seconds
                        ).isoformat()
                        if start_time
                        else None,
                        "duration_hours": duration_seconds / 3600
                        if duration_seconds
                        else None,
                    }
                )

            return standardized_contests
        else:
            print(f"Error fetching Codeforces contests: {response.status_code}")
            return []

    except Exception as e:
        print(f"Exception in get_codeforces_contests: {e}")
        return []


def get_codeforces_user_info(handle):

    url = f"{BASE_URL}user.info?handles={handle}"

    res = requests.get(url)

    data = res.json()
    result = data["result"][0]

    friends = result["friendOfCount"]
    maxRating = result.get("maxRating", "Unrated")
    maxRank = result.get("maxRank", "Unranked")
    rank = result.get("rank", "Unranked")

    return [friends, maxRating, maxRank, rank]


def get_recent_failed_problem_summaries(handle, limit=3):

    if handle:
        url = f"{BASE_URL}user.status?handle={handle}"
        res = requests.get(url)

        if res.status_code != 200:
            return []

        submissions = res.json().get("result", [])

        problems = {}

        for sub in submissions:
            verdict = sub.get("verdict")
            if verdict == "OK":
                continue

            problem = sub.get("problem", {})
            contest_id = problem.get("contestId")
            index = problem.get("index")

            if contest_id is None or index is None:
                continue

            problem_id = f"{contest_id}{index}"

            if problem_id not in problems:
                problems[problem_id] = {
                    "problem_id": problem_id,
                    "name": problem.get("name"),
                    "rating": problem.get("rating"),
                    "tags": problem.get("tags", []),
                    "failed_attempts": 0,
                    "verdicts": defaultdict(int),
                    "last_failed_at": 0,
                    "languages_used": set(),
                }

            summary = problems[problem_id]
            summary["failed_attempts"] += 1
            summary["verdicts"][verdict] += 1
            summary["last_failed_at"] = max(
                summary["last_failed_at"], sub.get("creationTimeSeconds", 0)
            )
            summary["languages_used"].add(sub.get("programmingLanguage"))

        summaries = []
        for p in problems.values():
            summaries.append(
                {
                    "problem_id": p["problem_id"],
                    "name": p["name"],
                    "rating": p["rating"],
                    "tags": p["tags"],
                    "failed_attempts": p["failed_attempts"],
                    "verdicts": dict(p["verdicts"]),
                    "last_failed_at": p["last_failed_at"],
                    "languages_used": list(p["languages_used"]),
                }
            )

        summaries.sort(key=lambda x: x["last_failed_at"], reverse=True)

        return summaries[:limit]
    else:
        return {}


def get_most_used_lang(handle):

    url = f"{BASE_URL}user.status?handle={handle}"
    res = requests.get(url)

    if res.status_code == 200:
        data = res.json()["result"]

        lang_count = {}
        for result in data:
            lang_count[result["programmingLanguage"]] = (
                lang_count.get(result["programmingLanguage"], 0) + 1
            )

    return max(lang_count, key=lang_count.get)


def get_all_accepted_submissions(handle):
    url = f"{BASE_URL}user.status?handle={handle}"
    res = requests.get(url)

    if res.status_code == 200:
        data = res.json()["result"]

        accepted = [s for s in data if s["verdict"] == "OK"]

        unique_problems = {}
        for sub in accepted:
            problem_id = f"{sub['problem']['contestId']}{sub['problem']['index']}"
            if problem_id not in unique_problems:
                unique_problems[problem_id] = sub["problem"]

        return list(unique_problems.values())
    return []


def get_topic_distribution(handle):
    solved_problems = get_all_accepted_submissions(handle)

    topic_counts = {}
    for problem in solved_problems:
        for tag in problem.get("tags", []):
            topic_counts[tag] = topic_counts.get(tag, 0) + 1

    return topic_counts, len(solved_problems)


def get_rating_history(handle):
    url = f"{BASE_URL}user.rating?handle={handle}"
    res = requests.get(url)

    if res.status_code == 200:
        contests = res.json()["result"]

        return [
            {
                "date": c["ratingUpdateTimeSeconds"],
                "rating": c["newRating"],
            }
            for c in contests
        ]

    return []


def get_blog_info(handle):

    url = f"{BASE_URL}user.blogEntries?handle={handle}"
    res = requests.get(url)

    if res.status_code == 200:
        data = res.json()["result"]

        count = len(data)
        ratings = {}

        for result in data:
            ratings[result["title"]] = result["rating"]

    return count, ratings


def get_full_codeforces_profile_stats(handle):

    try:
        data = {}

        if handle:
            tags_info, solved = get_topic_distribution(handle)
            most_used_tag = max(tags_info, key=tags_info.get)

            data["most_used_tag"] = most_used_tag

            profile_data = get_codeforces_user_info(handle)
            data["maxRating"] = profile_data[1]
            data["maxRank"] = profile_data[2]
            data["rank"] = profile_data[3]

            lang_data = get_most_used_lang(handle)
            data["most_used_lang"] = lang_data
            data["total_solved"] = solved

            blog_count, ratings = get_blog_info(handle)

            data["blog_count"] = blog_count
            data["best_rated_blog"] = max(ratings, key=ratings.get)
            data["best_rated_blog_ratings"] = ratings[data["best_rated_blog"]]

            ratingHistory = get_rating_history(handle)
            data["ratingHistory"] = ratingHistory

        return data

    except Exception as e:
        print(f"FROM get_full_codeforces_stats: {str(e)}")
        return {}


"""
LEETCODE!!
"""


def get_leetcode_submissions(username, accepted_only=False):

    try:
        if username:
            endpoint = (
                f"/leetcode/{username}/acSubmission"
                if accepted_only
                else f"/leetcode/{username}/submission"
            )
            url = f"{API_BASE}{endpoint}"
            res = requests.get(url)

            if res.status_code == 200:
                return res.json()["data"]
            else:
                return res.json()
        else:
            return {}
    except Exception as e:
        print(f"Error from leetcode submissions info {str(e)}")
        return {}


def get_recent_failed_leetcode_problems(submissions, limit=3):

    problems = {}
    if submissions:
        for sub in submissions:
            slug = sub.get("titleSlug")
            title = sub.get("title")
            verdict = sub.get("statusDisplay")
            ts = int(sub.get("timestamp", 0))
            lang = sub.get("lang")

            if not slug or not verdict:
                continue

            if slug not in problems:
                problems[slug] = {
                    "problem_slug": slug,
                    "title": title,
                    "failed_attempts": 0,
                    "verdicts": defaultdict(int),
                    "eventually_accepted": False,
                    "last_submission_ts": 0,
                    "languages_used": set(),
                }

            p = problems[slug]

            p["last_submission_ts"] = max(p["last_submission_ts"], ts)
            p["languages_used"].add(lang)

            if verdict == "Accepted":
                p["eventually_accepted"] = True
            else:
                p["failed_attempts"] += 1
                p["verdicts"][verdict] += 1

        failed_problems = [
            {
                "problem_slug": p["problem_slug"],
                "title": p["title"],
                "failed_attempts": p["failed_attempts"],
                "verdicts": dict(p["verdicts"]),
                "eventually_accepted": p["eventually_accepted"],
                "last_submission_ts": p["last_submission_ts"],
                "languages_used": list(p["languages_used"]),
            }
            for p in problems.values()
            if p["failed_attempts"] > 0
        ]

        failed_problems.sort(key=lambda x: x["last_submission_ts"], reverse=True)

        return failed_problems[:limit]
    else:
        return {}


def get_leetcode_tag_distribution(username):
    tag_mapping = {
        "math": "math",
        "greedy": "greedy",
        "dynamic-programming": "dp",
        "dp": "dp",
        "graph": "graphs",
        "tree": "trees",
        "binary-tree": "trees",
        "binary-search": "binary search",
        "depth-first-search": "dfs and similar",
        "dfs": "dfs and similar",
        "breadth-first-search": "dfs and similar",
        "bfs": "dfs and similar",
        "string": "strings",
        "two-pointers": "two pointers",
        "hash-table": "hashing",
        "sorting": "sortings",
        "bit-manipulation": "bitmasks",
        "geometry": "geometry",
        "combinatorics": "combinatorics",
        "number-theory": "number theory",
        "array": "data structures",
        "matrix": "data structures",
        "linked-list": "data structures",
        "stack": "data structures",
        "queue": "data structures",
        "heap": "data structures",
        "hash-map": "data structures",
        "trie": "data structures",
        "segment-tree": "data structures",
        "binary-indexed-tree": "data structures",
        "union-find": "data structures",
        "design": "data structures",
        "backtracking": "brute force",
        "divide-and-conquer": "brute force",
        "recursion": "brute force",
        "simulation": "brute force",
        "sliding-window": "two pointers",
        "prefix-sum": "data structures",
        "monotonic-stack": "data structures",
        "monotonic-queue": "data structures",
        "topological-sort": "graphs",
        "quickselect": "sortings",
    }

    try:
        skill_url = f"{API_BASE}/leetcode/skillStats/{username}"
        skill_res = requests.get(skill_url)

        if skill_res.status_code == 200:
            skill_data = skill_res.json()

            tag_data = skill_data.get("data", {})

            tag_counts = {}

            for difficulty_level in ["fundamental", "intermediate", "advanced"]:
                if difficulty_level in tag_data:
                    for tag_info in tag_data[difficulty_level]:
                        leetcode_tag = tag_info.get("tagSlug", "").lower()
                        problems_solved = tag_info.get("problemsSolved", 0)

                        if problems_solved > 0:
                            standardized_tag = tag_mapping.get(
                                leetcode_tag, leetcode_tag
                            )

                            if standardized_tag in tags_list_all:
                                tag_counts[standardized_tag] = (
                                    tag_counts.get(standardized_tag, 0)
                                    + problems_solved
                                )

            return {tag: count for tag, count in tag_counts.items() if count > 0}

        else:
            print(f"Error fetching LeetCode skill stats: {skill_res.status_code}")
            return {}
    except Exception as e:
        print(f"Error from leetcode tag distro: {str(e)}")
        return {}


def get_leetcode_most_used_language(username):

    try:
        endpoint = f"/leetcode/{username}/acSubmission"
        url = f"{API_BASE}{endpoint}"
        res = requests.get(url)

        if res.status_code == 200:
            data = res.json()
            submissions = data.get("data", [])

            language_counts = {}
            for submission in submissions:
                lang = submission.get("lang", "Unknown")
                language_counts[lang] = language_counts.get(lang, 0) + 1

            if language_counts:
                most_used = max(language_counts.items(), key=lambda x: x[1])
                return {
                    "language": most_used[0],
                    "count": most_used[1],
                    "percentage": round((most_used[1] / len(submissions)) * 100, 2),
                    "all_languages": language_counts,
                }
            else:
                return {
                    "language": "None",
                    "count": 0,
                    "percentage": 0,
                    "all_languages": {},
                }

        else:
            print(f"Error fetching LeetCode submissions: {res.status_code}")
            return {
                "language": "Unknown",
                "count": 0,
                "percentage": 0,
                "all_languages": {},
            }
    except Exception as e:
        print(f"Error from leetcode most used lang: {str(e)}")
        return {"language": "Unknown", "count": 0, "percentage": 0, "all_languages": {}}


def get_leetcode_submission_info(username):

    try:
        url = f"https://alfa-leetcode-api.onrender.com/{username}/profile"
        res = requests.get(url)

        if res.status_code == 200:
            return res.json()
        else:
            print(f"STATUS CODE: {res.status_code}")
            return {}
    except Exception as e:
        return {}


def get_full_leetcode_profile_stats(username):

    if username:
        data = {}
        data = get_leetcode_submission_info(username)

        langStats = get_leetcode_most_used_language(username)

        data["most_used_lang"] = langStats["language"]

        tag_data = get_leetcode_tag_distribution(username)

        most_used_tag = max(tag_data, key=tag_data.get)
        data["most_used_tag"] = most_used_tag

        return data
    else:
        return {}


def get_leetcode_contests():
    url = f"https://competeapi.vercel.app/contests/leetcode/"

    res = requests.get(url)

    if res.status_code == 200:
        data = res.json()["data"]["topTwoContests"]

        return data
    else:
        return {}


def get_leetcode_daily_challenge():
    url = f"{API_BASE}/leetcode/daily"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            problem = data.get("question", {})

            return {
                "platform": "leetcode",
                "title": problem.get("title", ""),
                "titleSlug": problem.get("titleSlug", ""),
                "difficulty": problem.get("difficulty", "UNKNOWN").lower(),
                "rating": None,
                "tags": [tag.get("name", "") for tag in problem.get("topicTags", [])],
                "link": f"https://leetcode.com/problems/{problem.get('titleSlug', '')}",
                "isPremium": False,
                "acRate": problem.get("acRate", 0),
                "is_contest": False,
                "contest_start": None,
                "contest_end": None,
                "is_daily": True,
            }
        else:
            print(f"Error fetching daily challenge: {response.status_code}")
            return None

    except Exception as e:
        print(f"Exception in get_leetcode_daily_challenge: {e}")
        return None


def get_leetcode_problems(tags=None, difficulty=None, limit=50, skip=0):
    base_url = f"{API_BASE}/leetcode/problems"

    params = []
    if tags:
        tags_str = "+".join(tags)
        params.append(f"tags={tags_str}")
    if difficulty:
        params.append(f"difficulty={difficulty.upper()}")
    if limit:
        params.append(f"limit={limit}")
    if skip:
        params.append(f"skip={skip}")

    url = base_url
    if params:
        url += "?" + "&".join(params)

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            problems = data["data"]["questions"]

            standardized_problems = []
            for problem in problems:
                standardized_problems.append(
                    {
                        "platform": "leetcode",
                        "title": problem.get("title", ""),
                        "titleSlug": problem.get("titleSlug", ""),
                        "difficulty": problem.get("difficulty", "UNKNOWN").lower(),
                        "rating": None,
                        "tags": [
                            tag.get("name", "") for tag in problem.get("topicTags", [])
                        ],
                        "link": f"https://leetcode.com/problems/{problem.get('titleSlug', '')}",
                        "isPremium": problem.get("isPaidOnly", False),
                        "acRate": problem.get("acRate", 0),
                        "is_contest": False,
                        "contest_start": None,
                        "contest_end": None,
                    }
                )

            return standardized_problems
        else:
            print(f"Error fetching LeetCode problems: {response.status_code}")
            return []

    except Exception as e:
        print(f"Exception in get_leetcode_problems: {e}")
        return []


"""
CODECHEF!!
"""


def get_codechef_profile_stats(username):

    data = {}

    if username:
        res = requests.get(f"https://competeapi.vercel.app/user/codechef/{username}/")

        if res.status_code == 200:
            data = res.json()

    return data


def get_codechef_contests():
    url = f"https://competeapi.vercel.app/contests/codechef/"

    res = requests.get(url)

    if res.status_code == 200:
        data = res.json()

        return data["future_contests"]
    else:
        return {}


def get_unified_tag_distribution(leetcode_username=None, codeforces_handle=None):
    standard_tags = [
        "data structures",
        "strings",
        "brute force",
        "sortings",
        "two pointers",
        "trees",
        "hashing",
        "greedy",
        "binary search",
        "dfs and similar",
        "bitmasks",
        "math",
        "dp",
        "graphs",
        "geometry",
        "combinatorics",
        "number theory",
    ]

    cf_tag_mapping = {
        "implementation": "brute force",
        "brute force": "brute force",
        "data structures": "data structures",
        "dp": "dp",
        "dynamic programming": "dp",
        "greedy": "greedy",
        "math": "math",
        "sortings": "sortings",
        "sorting": "sortings",
        "constructive algorithms": "brute force",
        "strings": "strings",
        "string": "strings",
        "two pointers": "two pointers",
        "combinatorics": "combinatorics",
        "graphs": "graphs",
        "graph": "graphs",
        "dfs and similar": "dfs and similar",
        "dfs": "dfs and similar",
        "bfs": "dfs and similar",
        "trees": "trees",
        "tree": "trees",
        "geometry": "geometry",
        "dsu": "data structures",
        "flows": "graphs",
        "graph matchings": "graphs",
        "hashing": "hashing",
        "number theory": "number theory",
        "bitmasks": "bitmasks",
        "bit manipulation": "bitmasks",
        "binary search": "binary search",
        "divide and conquer": "brute force",
        "games": "math",
        "shortest paths": "graphs",
        "matrices": "data structures",
        "ternary search": "binary search",
        "probabilities": "math",
        "chinese remainder theorem": "number theory",
        "*special": None,
        "string suffix structures": "strings",
        "expression parsing": "strings",
    }

    unified_distribution = {tag: 0 for tag in standard_tags}

    if leetcode_username:
        try:
            lc_tags = get_leetcode_tag_distribution(leetcode_username)
            for tag, count in lc_tags.items():
                if tag in unified_distribution:
                    unified_distribution[tag] += count
        except Exception as e:
            print(f"Error fetching LeetCode tags: {e}")

    if codeforces_handle:
        try:
            cf_tags, _ = get_topic_distribution(codeforces_handle)
            for cf_tag, count in cf_tags.items():
                standard_tag = cf_tag_mapping.get(cf_tag.lower())

                if standard_tag and standard_tag in unified_distribution:
                    unified_distribution[standard_tag] += count
        except Exception as e:
            print(f"Error fetching Codeforces tags: {e}")

    return {tag: count for tag, count in unified_distribution.items() if count > 0}


def get_unified_problem_recommendations(
    tags=None,
    difficulty=None,
    min_rating=None,
    max_rating=None,
    limit_per_platform=20,
    include_contests=True,
    platforms=["leetcode", "codeforces", "codechef"],
):

    leetcode_tag_map = {
        "dp": "dynamic-programming",
        "data structures": "array",
        "dfs and similar": "depth-first-search",
        "graphs": "graph",
        "trees": "tree",
        "strings": "string",
        "two pointers": "two-pointers",
        "hashing": "hash-table",
        "sortings": "sorting",
        "bitmasks": "bit-manipulation",
        "number theory": "number-theory",
        "binary search": "binary-search",
        "greedy": "greedy",
        "math": "math",
        "brute force": "backtracking",
    }

    codeforces_tag_map = {
        "dp": "dp",
        "data structures": "data structures",
        "dfs and similar": "dfs and similar",
        "graphs": "graphs",
        "trees": "trees",
        "strings": "strings",
        "two pointers": "two pointers",
        "hashing": "hashing",
        "sortings": "sortings",
        "bitmasks": "bitmasks",
        "number theory": "number theory",
        "binary search": "binary search",
        "greedy": "greedy",
        "math": "math",
        "brute force": "brute force",
        "combinatorics": "combinatorics",
        "geometry": "geometry",
    }

    all_problems = []
    all_contests = []

    if "leetcode" in platforms:
        try:
            lc_tags = None
            if tags:
                lc_tags = [leetcode_tag_map.get(tag, tag) for tag in tags]

            lc_problems = get_leetcode_problems(
                tags=lc_tags,
                difficulty=difficulty.upper() if difficulty else None,
                limit=limit_per_platform,
            )
            all_problems.extend(lc_problems)

            daily = get_leetcode_daily_challenge()
            if daily:
                all_problems.insert(0, daily)

            if include_contests:
                lc_contests_raw = get_leetcode_contests()
                for contest in lc_contests_raw:
                    all_contests.append(
                        {
                            "platform": "leetcode",
                            "title": contest.get("title", ""),
                            "link": f"https://leetcode.com/contest/{contest.get('title', '').lower().replace(' ', '-')}",
                            "is_contest": True,
                            "contest_start": datetime.fromtimestamp(
                                contest.get("startTime", 0)
                            ).isoformat(),
                            "contest_end": datetime.fromtimestamp(
                                contest.get("startTime", 0) + contest.get("duration", 0)
                            ).isoformat(),
                            "duration_hours": contest.get("duration", 0) / 3600,
                            "tags": [],
                            "difficulty": None,
                            "rating": None,
                        }
                    )

        except Exception as e:
            print(f"Error fetching LeetCode data: {e}")

    if "codeforces" in platforms:
        try:
            cf_tags = None
            if tags:
                cf_tags = [codeforces_tag_map.get(tag, tag) for tag in tags]

            if difficulty and not min_rating and not max_rating:
                if difficulty == "easy":
                    min_rating, max_rating = 800, 1200
                elif difficulty == "medium":
                    min_rating, max_rating = 1300, 1900
                elif difficulty == "hard":
                    min_rating, max_rating = 2000, 3500

            cf_problems = get_codeforces_problems(
                tags=[cf_tags[0]] if cf_tags else None,
                min_rating=min_rating if difficulty else None,
                max_rating=max_rating,
                limit=limit_per_platform,
            )
            all_problems.extend(cf_problems)

            if include_contests:
                cf_contests = get_codeforces_contests(upcoming=True)
                all_contests.extend(cf_contests)

        except Exception as e:
            print(f"Error fetching Codeforces data: {e}")

    if "codechef" in platforms and include_contests:
        try:
            cc_contests_raw = get_codechef_contests()
            for contest in cc_contests_raw:
                all_contests.append(
                    {
                        "platform": "codechef",
                        "title": contest.get("contest_name", ""),
                        "link": f"https://www.codechef.com/{contest.get('contest_code', '')}",
                        "is_contest": True,
                        "contest_start": contest.get("contest_start_date_iso", ""),
                        "contest_end": contest.get("contest_end_date_iso", ""),
                        "duration_hours": int(contest.get("contest_duration", 0)) / 60,
                        "tags": [],
                        "difficulty": None,
                        "rating": None,
                    }
                )

        except Exception as e:
            print(f"Error fetching CodeChef data: {e}")

    def sort_key(problem):
        if problem["platform"] == "codeforces" and problem.get("rating"):
            return problem["rating"]
        elif problem["platform"] == "leetcode":
            diff_order = {"easy": 1, "medium": 2, "hard": 3, "unknown": 4}
            return diff_order.get(problem["difficulty"], 4) * 1000
        return 9999

    all_problems.sort(key=sort_key)

    all_contests.sort(key=lambda x: x.get("contest_start", ""))

    return {
        "problems": all_problems,
        "contests": all_contests,
        "total_problems": len(all_problems),
        "total_contests": len(all_contests),
    }
