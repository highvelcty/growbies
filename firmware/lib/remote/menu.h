#pragma once

#include <vector>
#include <memory>
#include <functional>

#include "drawing.h"

// Forward Declarations
class Remote;

// -----------------------------------------------------------------------------
// Menu items
// -----------------------------------------------------------------------------
struct MenuItem {
    std::shared_ptr<Drawing> drawing;
    std::vector<std::shared_ptr<MenuItem>> children;
    std::function<void()> action;

    explicit MenuItem(std::shared_ptr<Drawing> d,
             std::vector<std::shared_ptr<MenuItem>> c = {},
             std::function<void()> a = {})
        : drawing(std::move(d)), children(std::move(c)), action(std::move(a)) {}

    virtual size_t on_descent() const {
        return 0;
    }

    virtual void on_select() const {}

    virtual ~MenuItem() = default;
};

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

extern const std::vector<std::shared_ptr<MenuItem>> menu_root;
