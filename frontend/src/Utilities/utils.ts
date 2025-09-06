/**
 * Debounce function: returns a new function that delays the execution of the given function `fn`
 * until after `delay` milliseconds have elapsed since the last time it was invoked.
 *
 * @param fn    - Function to debounce.
 * @param delay - Delay time in milliseconds.
 * @returns     - Debounced version of `fn`.
 */
export function debounce<T extends (...args: any[]) => void>(
    fn: T,
    delay = 300
): (...args: Parameters<T>) => void {
    let timer: ReturnType<typeof setTimeout> | null = null;

    return (...args: Parameters<T>) => {
        if (timer) {
            clearTimeout(timer);
        }
        timer = setTimeout(() => {
            fn(...args);
        }, delay);
    };
}

/**
 * Throttles a function so that it is only executed at most once every `limit` milliseconds.
 *
 * @param func - The function to be throttled.
 * @param limit - The time interval in milliseconds to limit the function execution.
 * @returns A throttled version of the provided function.
 */
export function throttle<T extends (...args: any[]) => void>(
    func: T,
    limit: number
): T {
    let lastFunc: ReturnType<typeof setTimeout>;
    let lastRan: number | null = null;

    return function (this: unknown, ...args: Parameters<T>) {
        const context = this;

        if (lastRan === null) {
            func.apply(context, args);
            lastRan = Date.now();
        } else {
            clearTimeout(lastFunc);
            lastFunc = setTimeout(() => {
                if (Date.now() - lastRan! >= limit) {
                    func.apply(context, args);
                    lastRan = Date.now();
                }
            }, limit - (Date.now() - lastRan));
        }
    } as T;
}

export enum TimeRange {
    ONE_WEEK = "1 week",
    ONE_MONTH = "1 month",
    THREE_MONTHS = "3 months",
    SIX_MONTHS = "6 months",
    ONE_YEAR = "1 year",
    TWO_YEARS = "2 years",
    YTD = "YTD",
}

/**
 * Returns a date range string in the format:
 *   From 16 Dec, 2024 to 23 Dec, 2024
 * where "to" is always the current date.
 */
export function getDateRange(range: TimeRange): [string, string] {
    const endDate = new Date(); // 'to' is always current date
    let startDate = new Date(); // we'll adjust this based on 'range'

    switch (range) {
        case TimeRange.ONE_WEEK:
            // subtract 7 days
            startDate.setDate(startDate.getDate() - 7);
            break;
        case TimeRange.ONE_MONTH:
            // subtract 1 month
            startDate.setMonth(startDate.getMonth() - 1);
            break;
        case TimeRange.THREE_MONTHS:
            // subtract 3 months
            startDate.setMonth(startDate.getMonth() - 3);
            break;
        case TimeRange.SIX_MONTHS:
            // subtract 6 months
            startDate.setMonth(startDate.getMonth() - 6);
            break;
        case TimeRange.ONE_YEAR:
            // subtract 12 months
            startDate.setFullYear(startDate.getFullYear() - 1);
            break;
        case TimeRange.TWO_YEARS:
            // subtract 24 months
            startDate.setFullYear(startDate.getFullYear() - 2);
            break;
        case TimeRange.YTD:
            // Year-to-date: from Jan 1 of this year
            startDate = new Date(startDate.getFullYear(), 0, 1);
            break;
        default:
            // If an unknown range is passed, default to "today only"
            startDate = endDate;
            break;
    }

    return [formatDisplayDate(startDate), formatDisplayDate(endDate)];
}

/**
 * Formats a Date to "DD MMM, YYYY"
 * Example: 16 Dec, 2024
 */
function formatDisplayDate(date: Date): string {
    // Options for toLocaleDateString
    // "en-GB" => day/month/year order
    const options: Intl.DateTimeFormatOptions = {
        day: "numeric",
        month: "short", // e.g. "Dec"
        year: "numeric",
    };
    // e.g. "16 Dec 2024"
    const partial = date.toLocaleDateString("en-GB", options);

    // Insert comma before the year => "16 Dec, 2024"
    // We'll do a small RegEx fix if you want a comma specifically after the month
    return partial.replace(/(\d+ \w+) (\d+)/, "$1, $2");
}

/**
 * Formats a price by rounding to an integer and adding thousand separators.
 * If input is NaN, null, undefined, or not a valid number, returns "-".
 *
 * Example:
 *   formatPrice(1234567.89) => "1,234,568"
 *   formatPrice(null)       => "-"
 *   formatPrice(NaN)        => "-"
 */
export function formatPrice(price: unknown, precision: number = 0): string {
    // Ensure the input is a valid number
    if (typeof price !== "number" || isNaN(price)) {
        return "-";
    }

    // Round to the nearest integer
    const coef = 10 ** precision;
    const roundedPrice = Math.round(price * coef) / coef;

    // Format with thousand separators
    return roundedPrice.toLocaleString("en-US");
}

/**
 * Extracts up to two numbers (including floats) from a given string.
 * Returns an array containing the first two numbers found, rounded to integers.
 * If less than two numbers are found, returns what is available.
 *
 * Example:
 *   extractTwoNumbers("aaaad 123.12 asdjhjkhqw qweq 312.56") => [123, 313]
 *   extractTwoNumbers("Price: 49.9 and discount: 5.2")       => [50, 5]
 *   extractTwoNumbers("Only one number: 777.8")             => [778]
 *   extractTwoNumbers("No numbers here!")                   => []
 */
export function extractTwoNumbers(input: string): number[] {
    // Match numbers, including decimals (e.g., 123.45)
    const matches = input.match(/\d+(\.\d+)?/g);

    // Convert matches to numbers, round them, and return the first two
    return matches
        ? matches.slice(0, 2).map((num) => Math.round(parseFloat(num)))
        : [];
}

export function formatPercent(number: number): string {
    const roundedNumber = Math.round(number * 100) / 100;
    const formattedNumber = roundedNumber.toFixed(2);

    if (roundedNumber > 0) {
        return `${formattedNumber}%`;
    } else {
        return `${formattedNumber}%`;
    }
}
