import pytest

def pytest_collection_modifyitems(items):
    # Map each test item to its module name
    module_mapping = [(item, item.module.__name__) for item in items]

    # Define the desired order of test modules
    MODULE_ORDER = [
        "test_graph_abstraction",
        "test_factory",
        "test_objects",
        "test_filters",
        "test_transformation",
        "test_params",
        "test_weird",
        ]

    # Initialize buckets for categorizing tests
    module_tests = {name: [] for name in MODULE_ORDER}
    rest_of_tests = []

    # Categorize tests into their respective buckets
    for item, mod_name in module_mapping:
        if mod_name in module_tests:
            module_tests[mod_name].append(item)
        else:
            rest_of_tests.append(item)

    # Construct the final ordered list
    # Why: Preserves specified module order while including all tests
    result = []
    for mod_name in MODULE_ORDER:
        result += module_tests[mod_name]

    result += rest_of_tests

    # debug:
    # from pprint import pprint
    # pprint(items)
    # pprint(result)

    # Replace the original unordered list with our ordered list
    items[:] = result
