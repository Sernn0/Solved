#include <string>
#include <vector>
#include <algorithm>

using namespace std;

vector<int> solution(int n) {
    vector<int> answer;
    while(1) {
        for (int i=2; i<=n; i++) {
            if(n % i == 0) {
                if(find(answer.begin(), answer.end(), i) == answer.end()) {
                    answer.push_back(i);
                }
                n = n / i;
                break;
            }
        }
        if(n == 1) {
            sort(answer.begin(), answer.end());
            break;
        }
    }
    return answer;
}