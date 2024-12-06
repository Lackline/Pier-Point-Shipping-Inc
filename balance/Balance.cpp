// Balance.cpp
#include "Balance.h"
#include <iostream>
#include <queue>
#include <unordered_map>
#include <cmath>
#include <iomanip>
#include <string>

using namespace std;

Balance::Balance(vector<vector<int>>& initialShip) : ship(initialShip) {}

int Balance::calculateHeuristic(int row, int col, int targetRow, int targetCol) {
    return abs(row - targetRow) + abs(col - targetCol); // 曼哈頓距離
}


vector<pair<int, int>> Balance::findShortestPath(int startRow, int startCol) {
    priority_queue<Node, vector<Node>, greater<Node>> openList;
    unordered_map<string, bool> visited;
    vector<pair<int, int>> directions = { {-1, 0}, {1, 0}, {0, -1}, {0, 1} };

    // if target on the left then move to right, if on the right then move to left
    bool moveToRight = (startCol < cols / 2);

    int targetCol = moveToRight ? cols / 2 : cols / 2 - 1;
    int targetRow = -1;

    if (moveToRight) {
        // if on the left then move to right
        while (targetCol >= cols / 2 && targetCol < cols) {
            for (int r = rows - 1; r >= 0; --r) { // start at the bottom
                if (ship[r][targetCol] == 0) {
                    if (r == rows - 1 || ship[r + 1][targetCol] != 0) {
                        targetRow = r;
                        break;
                    }
                }
            }
            if (targetRow != -1) break;
            --targetCol;
        }
    }
    else {
        // if on the right then move to left
        while (targetCol >= 0 && targetCol < cols / 2) {
            for (int r = rows - 1; r >= 0; --r) {
                if (ship[r][targetCol] == 0) {
                    if (r == rows - 1 || ship[r + 1][targetCol] != 0) {
                        targetRow = r;
                        break;
                    }
                }
            }
            if (targetRow != -1) break;
            ++targetCol;
        }
    }

    // if can't find target
    if (targetRow == -1) {
        cout << "can't find target。" << endl;
        return {};
    }

    // initialize node
    Node startNode = { startRow, startCol, 0, calculateHeuristic(startRow, startCol, targetRow, targetCol), {} };
    openList.push(startNode);

    while (!openList.empty()) {
        Node current = openList.top();
        openList.pop();

        // return if on goal state
        if (current.row == targetRow && current.col == targetCol) {
            return current.path;
        }

        string state = to_string(current.row) + "-" + to_string(current.col);
        if (visited[state]) continue;
        visited[state] = true;

        for (auto& dir : directions) {
            int newRow = current.row + dir.first;
            int newCol = current.col + dir.second;

            if (newRow < 0 || newRow >= rows || newCol < 0 || newCol >= cols) continue;
            if (visited[to_string(newRow) + "-" + to_string(newCol)]) continue;
            if (ship[newRow][newCol] != 0) continue; // don't go through obstacle

            int newG = current.g + 1;
            int newH = calculateHeuristic(newRow, newCol, targetRow, targetCol);

            Node newNode = { newRow, newCol, newG, newH, current.path };
            newNode.path.push_back({ newRow, newCol });
            openList.push(newNode);
        }
    }

    return {};
}



// calculate weights on two sides
void Balance::calculateSums() {
    leftSum = 0;
    rightSum = 0;
    totalSum = 0;

    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            if(ship[i][j] == -1){} // if it's NAN then ignore it
            else {
                totalSum += ship[i][j];
                if (j < cols / 2) {
                    leftSum += ship[i][j];
                }
                else {
                    rightSum += ship[i][j];
                }
            }
        }
    }
}

void Balance::printShipWeight(){
    cout << "weights on left half: " << leftSum << endl;
    cout << "weights on right half: " << rightSum << endl;
    cout << "total weight: " << totalSum << endl;
}


void Balance::modifyShip(int row, int col, int value) {
    ship[row][col] = value;
}


int Balance::containerWeight(int row, int col) {
    return ship[row][col];
}


// check if ship is balance now
bool Balance::isBalanced() {
    if (opitimalBalance == true) {
        return true;
    }

    calculateSums();
    int totalWeight = leftSum + rightSum;

    if (totalWeight == 0) {
        return true;
    }

    int tolerance = totalWeight * 0.1; // 10%
    return abs(leftSum - rightSum) <= tolerance;
}





// print the best move route
void Balance::printBestMove() {
    pair<int, int> bestMove = findBestMove();

    if (previousBestMove == bestMove)
    {
        cout << "opitimal balance achived!" << endl;
        opitimalBalance = true;
        return;
    }
    else
    {
        int row = bestMove.first;
        int col = bestMove.second;

        auto path1 = findShortestPath(row, col);
        if (!path1.empty()) {
            cout << "target position:[" << row << "][" << col << "] = " << containerWeight(row, col) << endl;
            cout << "successful! here's the route：" << endl;
            for (size_t i = 0; i < path1.size(); ++i) {
                cout << "Step " << i + 1 << ": (" << path1[i].first << ", " << path1[i].second << ")" << endl;
            }
            modifyShip(path1[path1.size() - 1].first, path1[path1.size() - 1].second, containerWeight(row, col)); //move the weight
            previousBestMove = { path1[path1.size() - 1].first, path1[path1.size() - 1].second };
            modifyShip(row, col, 0); // clear origin spot
        }
        else {
            cout << "failed, can't find a route" << endl;
        }
    }
}

bool Balance::moveObstacle(int row, int col) {
    int targetCol = -1;

    cout << "adjusting the object position above the target [" << row << "][" << col << "] before moving the target" << endl;

    if (col >= cols / 2) { // right half
        if (col < cols - 1) {
            targetCol = col + 1; // moving one col to the right
        }
        else {
            targetCol = 6; // move to col6 if at col11
        }
    }
    else { // left half
        if (col > 0) {
            targetCol = col - 1; // moving one col to the left
        }
        else {
            targetCol = 5; // move to col5 if at col0
        }
    }

    // put it at the bottom so no floating object
    for (int targetRow = rows - 1; targetRow >= 0; --targetRow) {
        if (ship[targetRow][targetCol] == 0) { // empty spot
            ship[targetRow][targetCol] = ship[row][col];
            ship[row][col] = 0;
            return true;
        }
    }
    return false;
}



//find which is the best target to move
pair<int, int> Balance::findBestMove() {
    int middleNumber = totalSum / 2;
    pair<int, int> bestMove = { -1, -1 };
    int closestDiff = INT_MAX;
    const int threshold = 1;

    if (leftSum > rightSum) {
        for (int i = 0; i < rows; ++i) {
            for (int j = 0; j < cols / 2; ++j) {
                int weight = ship[i][j];
                // skip NAN(-1)
                if (weight != 0 && weight != -1) {
                    // check no object above target
                    for (int r = 0; r < i; ++r) {
                        if (ship[r][j] > 0) {
                            if (!moveObstacle(r, j)) {
                                cerr << "Error: Unable to move obstacle at (" << r << ", " << j << ")." << endl;
                                return { -1, -1 };
                            }
                        }
                    }

                    vector<pair<int, int>> path = findShortestPath(i, j);
                    if (!path.empty()) {
                        int tempRightSum = rightSum + weight;
                        int diff = abs(tempRightSum - middleNumber);
                        if (diff < closestDiff) {
                            closestDiff = diff;
                            bestMove = { i, j };
                        }
                        if (diff <= threshold) {
                            return bestMove;
                        }
                    }
                }
            }
        }
    }
    else {
        for (int i = 0; i < rows; ++i) {
            for (int j = cols / 2; j < cols; ++j) {
                int weight = ship[i][j];
                // skip NAN(-1)
                if (weight != 0 && weight != -1) {
                    // check no object above target
                    for (int r = 0; r < i; ++r) {
                        if (ship[r][j] > 0) {
                            if (!moveObstacle(r, j)) {
                                cerr << "Error: Unable to move obstacle at (" << r << ", " << j << ").\n";
                                return { -1, -1 };
                            }
                        }
                    }

                    vector<pair<int, int>> path = findShortestPath(i, j);
                    if (!path.empty()) {
                        int tempLeftSum = leftSum + weight;
                        int diff = abs(tempLeftSum - middleNumber);
                        if (diff < closestDiff) {
                            closestDiff = diff;
                            bestMove = { i, j };
                        }
                        if (diff <= threshold) {
                            return bestMove;
                        }
                    }
                }
            }
        }
    }
    return bestMove;
}




void Balance::printShip() {
    cout << "current ship:" << endl;
    for (int i = 0; i < ship.size(); i++) {
        for (int j = 0; j < ship[i].size(); j++) {
            cout << setw(5) << ship[i][j] << " ";
        }
        cout << endl;
    }
}