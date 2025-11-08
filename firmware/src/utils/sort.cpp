#include "sort.h"

void insertion_sort(float* arr, const int size) {
    for (int i = 1; i < size; ++i) {
        const float key = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = key;
    }
}
