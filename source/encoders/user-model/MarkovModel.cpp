#include "MarkovModel.h"

#include <algorithm>
#include <array>

constexpr bool rowIsValid(const std::array<double, 3> &array) {
    int sum = 0;
    for (double val : array) {
        // cppcheck-suppress useStlAlgorithm
        sum += static_cast<int>(val * 100.0);
    }
    return sum == 100;
}

constexpr static std::array<std::array<double, 3>, 3> transitionWeights{{
    {0.1, 0.3, 0.6},  // fetch
    {0.5, 0.2, 0.3},  // post
    {0.7, 0.2, 0.1},  // wait
}};
static_assert(rowIsValid(transitionWeights.at(0)));
static_assert(rowIsValid(transitionWeights.at(1)));
static_assert(rowIsValid(transitionWeights.at(2)));

MarkovModel::UserAction MarkovModel::getNextUserAction() {
    int nextState = 0;
    auto weights = transitionWeights.at(static_cast<size_t>(currentState));
    double cumSum = 0.0;
    double random = getRandom();
    for (size_t i = 0; i < weights.size(); ++i) {
        cumSum += weights.at(i);
        if (cumSum > random) {
            nextState = i;
            break;
        }
    }
    currentState = nextState;
    return static_cast<UserAction>(currentState);
}

double MarkovModel::getRandom() {
    return std::generate_canonical<double, 10>(gen);
}