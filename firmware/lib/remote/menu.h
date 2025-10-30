#pragma once

#include <vector>
#include <memory>

#include "drawing.h"

// Forward Declarations
class Remote;
struct MenuItem;

class Menu {
public:
    explicit Menu(Remote& r) : remote(r) {}

    void up();
    void down();
    void select();
    void render() const;

private:
    const std::vector<std::shared_ptr<MenuItem>>* level_from_path() const;

    std::vector<size_t> menu_path{0};  // Index path down the tree
    Remote& remote;
};
