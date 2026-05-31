#include <iostream>
#include <string>
#include <cctype>

using namespace std;

int main(void) {
    string str;
    cin >> str;
    
    for(int i=0; i<str.length(); i++){
        if('a' <= str[i] && str[i] <= 'z') cout << (char)toupper(str[i]);
        else if ('A' <= str[i] && str[i] <= 'Z') cout << (char)tolower(str[i]);
    }
    return 0;
}