#pragma once

template <typename Base, typename Derived>
struct is_base_of {
private:
    static char test(const Base*);
    static int test(...);
public:
    static const bool value = sizeof(test(static_cast<Derived*>(nullptr))) == sizeof(char);
};
