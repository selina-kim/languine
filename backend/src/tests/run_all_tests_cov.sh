#!/bin/bash

# Test runner with individual coverage for each test file
# Tests are run via docker compose and results are aggregated

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_SKIPPED=0
TOTAL_ERRORS=0
SUMMARY=()
FAILED_TESTS=()
COVERAGE_ROWS=()  # "test_name|path|stmts|miss|pct" — one entry per covered file

# Format: "test_file:coverage_module:marker"
TESTS=(
    "test_auth_integration.py:routes.auth:integration"
    "test_auth_unit.py:services.auth_service:not_integration"
    "test_builtin_decks_integration.py:db:integration"
    "test_card_integration.py:routes.cards:integration"
    "test_card_unit.py:services.card_service:not_integration"
    "test_create_deck_integration.py:routes.decks:integration"
    "test_deck_import_export_unit.py:services.deck_import_export_service:not_integration"
    "test_decks_integration.py:routes.decks:integration"
    "test_decks_unit.py:services.deck_service:not_integration"
    "test_dictionary_integration.py:services.dictionary_service:integration"
    "test_dictionary_unit.py:services.dictionary_service:not_integration"
    "test_fsrs.py:services.fsrs:not_integration"
    "test_fsrs_optimizer.py:services.fsrs.optimizer:not_integration"
    "test_fsrs_routes_integration.py:routes.fsrs:integration"
    "test_fsrs_service_unit.py:services.fsrs_service:not_integration"
    "test_images_integration.py:routes.images:integration"
    "test_images_unit.py:services.image_service:not_integration"
    "test_translate_integration.py:services.translate_service:integration"
    "test_translate_unit.py:services.translate_service:not_integration"
    "test_tts_integration.py:services.tts_service:integration"
    "test_tts_unit.py:services.tts_service:not_integration"
    "test_user_integration.py:routes.users:integration"
    "test_user_unit.py:services.user_service:not_integration"
)

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Running Tests with Coverage${NC}"
echo -e "${BLUE}================================${NC}\n"

cd "$(dirname "$0")"

for entry in "${TESTS[@]}"; do
    test_name=$(echo "$entry" | cut -d: -f1)
    coverage_module=$(echo "$entry" | cut -d: -f2)
    marker=$(echo "$entry" | cut -d: -f3)
    test_file="src/tests/$test_name"

    echo -e "${YELLOW}Running: $test_name${NC}"

    if [ "$marker" = "integration" ]; then
        pytest_cmd="pytest \"$test_file\" --cov=\"$coverage_module\" --override-ini=addopts= -m integration -v"
    else
        pytest_cmd="pytest \"$test_file\" --cov=\"$coverage_module\" -v"
    fi

    if output=$(docker compose exec backend bash -c "$pytest_cmd" 2>&1); then
        exit_ok=true
    else
        exit_ok=false
    fi

    if [[ $output =~ ([0-9]+)\ passed ]];  then passed="${BASH_REMATCH[1]}";  else passed=0;  fi
    if [[ $output =~ ([0-9]+)\ failed ]];  then failed="${BASH_REMATCH[1]}";  else failed=0;  fi
    if [[ $output =~ ([0-9]+)\ skipped ]]; then skipped="${BASH_REMATCH[1]}"; else skipped=0; fi
    if [[ $output =~ ([0-9]+)\ error ]];   then errors="${BASH_REMATCH[1]}";  else errors=0;  fi

    TOTAL_PASSED=$((TOTAL_PASSED + passed))
    TOTAL_FAILED=$((TOTAL_FAILED + failed))
    TOTAL_SKIPPED=$((TOTAL_SKIPPED + skipped))
    TOTAL_ERRORS=$((TOTAL_ERRORS + errors))

    # Extract individual failed test names from verbose output
    while IFS= read -r line; do
        [ -n "$line" ] && FAILED_TESTS+=("$line")
    done < <(echo "$output" | grep -E "FAILED " | sed 's/ FAILED.*//')

    # Capture all per-file coverage lines into COVERAGE_ROWS
    while IFS= read -r cov_line; do
        [ -z "$cov_line" ] && continue
        cp=$(echo "$cov_line" | awk '{print $1}')
        cs=$(echo "$cov_line" | awk '{print $2}')
        cm=$(echo "$cov_line" | awk '{print $3}')
        cpct=$(echo "$cov_line" | awk '{print $4}')
        COVERAGE_ROWS+=("$test_name|$cp|$cs|$cm|$cpct")
    done < <(echo "$output" | grep -E "^src/.*[0-9]+%$")

    # For inline display: prefer TOTAL line (multi-file), fall back to first src/ line
    total_line=$(echo "$output" | grep -E "^TOTAL\b")
    if [ -n "$total_line" ]; then
        cov_pct=$(echo "$total_line" | awk '{print $4}')
    elif echo "$output" | grep -qE "^src/.*[0-9]+%$"; then
        cov_pct=$(echo "$output" | grep -E "^src/.*[0-9]+%$" | head -1 | awk '{print $4}')
    else
        cov_pct="N/A"
    fi
    cov_path="(see coverage table)"; cov_stmts="-"; cov_miss="-"

    if [ "$failed" -eq 0 ] && [ "$errors" -eq 0 ] && [ "$exit_ok" = true ]; then
        echo -e "  ${GREEN}✓ PASSED${NC} (${GREEN}$passed passed${NC}, ${YELLOW}$skipped skipped${NC})  coverage: $cov_pct\n"
        SUMMARY+=("PASS|$test_name|$cov_path|$passed|0|$skipped|$cov_stmts|$cov_miss|$cov_pct")
    else
        echo -e "  ${RED}✗ FAILED${NC} (${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}, ${YELLOW}$skipped skipped${NC})  coverage: $cov_pct\n"
        SUMMARY+=("FAIL|$test_name|$cov_path|$passed|$failed|$skipped|$cov_stmts|$cov_miss|$cov_pct")
    fi
done

# Print summary
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  TEST SUMMARY${NC}"
echo -e "${BLUE}================================${NC}\n"

for line in "${SUMMARY[@]}"; do
    status=$(echo "$line"  | cut -d'|' -f1)
    name=$(echo "$line"    | cut -d'|' -f2)
    passed=$(echo "$line"  | cut -d'|' -f4)
    failed=$(echo "$line"  | cut -d'|' -f5)
    skipped=$(echo "$line" | cut -d'|' -f6)

    if [ "$status" = "PASS" ]; then
        echo -e "  ${GREEN}✓${NC} $name  (${GREEN}$passed passed${NC}, ${YELLOW}$skipped skipped${NC})"
    else
        echo -e "  ${RED}✗${NC} $name  (${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}, ${YELLOW}$skipped skipped${NC})"
    fi
done

echo ""
echo -e "${BLUE}--------------------------------${NC}"
echo -e "  Total Passed:   ${GREEN}$TOTAL_PASSED${NC}"
echo -e "  Total Failed:   ${RED}$TOTAL_FAILED${NC}"
echo -e "  Total Skipped:  ${YELLOW}$TOTAL_SKIPPED${NC}"
echo -e "  Total Errors:   ${RED}$TOTAL_ERRORS${NC}"
echo -e "${BLUE}--------------------------------${NC}"

# Coverage table
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}  COVERAGE SUMMARY${NC}"
echo -e "${BLUE}================================${NC}"
printf "\n  %-34s  %-44s  %5s  %5s  %s\n" "Test File" "Path" "Stmts" "Miss" "Cover"
printf "  %-34s  %-44s  %5s  %5s  %s\n" "──────────────────────────────────" "────────────────────────────────────────────" "─────" "─────" "──────"
prev_test=""
for row in "${COVERAGE_ROWS[@]}"; do
    name=$(echo "$row"  | cut -d'|' -f1)
    path=$(echo "$row"  | cut -d'|' -f2)
    stmts=$(echo "$row" | cut -d'|' -f3)
    miss=$(echo "$row"  | cut -d'|' -f4)
    cov=$(echo "$row"   | cut -d'|' -f5)

    # Only show the test name on the first row for each test
    if [ "$name" = "$prev_test" ]; then
        display_name=""
    else
        display_name="$name"
        prev_test="$name"
    fi

    num=$(echo "$cov" | tr -d '%')
    if [ "$cov" = "N/A" ]; then
        cov_colored="${YELLOW}N/A${NC}"
    elif [ "$num" -ge 90 ] 2>/dev/null; then
        cov_colored="${GREEN}$cov${NC}"
    elif [ "$num" -ge 60 ] 2>/dev/null; then
        cov_colored="${YELLOW}$cov${NC}"
    else
        cov_colored="${RED}$cov${NC}"
    fi

    printf "  %-34s  %-44s  %5s  %5s  %b\n" "$display_name" "$path" "$stmts" "$miss" "$cov_colored"
done
echo ""

if [ "${#FAILED_TESTS[@]}" -gt 0 ]; then
    echo -e "\n${RED}Failed tests:${NC}"
    for t in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}✗${NC} $t"
    done
fi

if [ "$TOTAL_FAILED" -gt 0 ] || [ "$TOTAL_ERRORS" -gt 0 ]; then
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
fi
