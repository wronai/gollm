function sortArrayByProperty(arr, propertyName) {
    /**
     * Sorts an array of objects by a specified property.
     *
     * @param {array} arr The array to be sorted.
     * @param {string} propertyName The name of the property to sort by.
     * @returns {array} The sorted array.
     */
    return arr.sort((a, b) => {
        if (!a || !b) {
            // handle null or undefined values
            return 0;
        }
        const aValue = a[propertyName];
        const bValue = b[propertyName];
        if (typeof aValue !== 'string' && typeof bValue !== 'string') {
            // handle non-string property values
            return aValue.localeCompare(bValue);
        } else {
            // handle string property values
            return a[propertyName].localeCompare(b[propertyName]);
        }
    });
}

// Usage
console.log(sortArrayByProperty([{ foo: 1 }, { bar: 2 }, { baz: 3 }], 'foo'));