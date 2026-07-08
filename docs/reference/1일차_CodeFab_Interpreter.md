# CodeFab Interpreter 프로젝트 (1일차)

> `docs/reference/1일차_CodeFab Interpreter.pdf`를 Markdown으로 옮긴 문서. 원본 PDF는
> 슬라이드(이미지) 형식이라 매번 렌더링 비용이 크므로, 텍스트로 검색/참조하기 쉽도록
> 별도로 보관한다. 원본과 내용이 어긋나면 PDF가 우선한다.

## 목차 (Chapters)

1. Code Fab 프로젝트 개요
2. Assembler Unit 제작 (Tokenizer → Expression → Statement → 가공 작업)
3. Checker Unit 제작
4. Executor Unit 제작
5. 테스트용 스크립트
6. 팀 프로젝트 진행

---

## Chapter 1. CodeFab Interpreter 프로젝트 개요

### Code Fab이란?

- 인터프리터(Interpreter)를 의미. 파이썬의 Interpreter로 비유될 수 있음.
- Code를 넣으면 공장처럼 동작된다는 의미로 "Code Fab"이라 이름 지음.
- 흐름: `스크립트` → `LangFactory(=Code Fab)` → `실행결과`

### 프로젝트 목표

1. **Custom Language 개발** — 팀 전용 커스텀 프로그래밍 언어를 제작한다.
2. **Code Fab (Interpreter) 개발** — Custom Language로 동작되는 인터프리터를 제작해
   실행되게끔 한다.
   - 1. Custom Language 제작: 팀에서 커스텀 프로그래밍 언어를 만든다.
   - 2. Code Fab 동작 순서: 문법을 트리 구조로 만들기 → 오류검증 → 트리구조대로 실행하기.
3. **Prompt Shell 제작** — CLI Shell을 제작하여 Custom Language를 사용해 즉시 결과를
   확인할 수 있게 한다 (예: 파이썬 REPL과 유사한 `>>>` 프롬프트).

### 프로젝트 진행 방향

- **1~2일차**: Custom Language 제작 / Code Fab 제작 / Prompt Shell 제작
- **3~4일차**: 기능 추가 예정
- **5일차**: 프로젝트 발표

### 좋지 않은 Custom Language 예시

`#define`을 남용해 `e`, `ee`, `eee` 같은 의미 없는 매크로로 C++ 문법을 완전히 가려버린
코드 스니펫에 빨간 X 표시와 "NO!!!" 캡션을 붙여 반면교사로 제시 — 가독성 없는 난독화된
커스텀 언어는 지양한다는 취지.

### Code Fab의 구성요소

Code Fab은 파이프라인을 갖춘 공장처럼 동작되는 인터프리터이며, 총 3개의 Unit으로
구성된다: **Assembler Unit → Checker Unit → Executor Unit**.

| Unit | 역할 |
|---|---|
| Assembler Unit | 소스코드를 입력받아 부품(Token)들로 분해한 뒤, 가공하여 Tree 구조 조립체를 만든다. |
| Checker Unit | 조립체를 실행하기 전에 오류 및 경고를 검출한다. |
| Executor Unit | 조립체를 실제로 실행하여 실행 결과를 낸다. |

### Assembly Unit 핵심원리 — Token화

**Token (부품으로 비유)**: 소스코드를 의미 있는 단위로 잘라낸 조각.

Token의 종류:
- 키워드 (예: `if`, `for`, `return`)
- 식별자(Identifier) (예: 변수이름, 함수이름)
- 리터럴 (숫자, 문자열)
- 연산자 (`+ - * /` 등)
- 구분자 (문장 끝 or 블록 구분: `; } {` 괄호 등)

```
var a = 3;   →  [var] [a] [=] [3] [;]
```

### Assembly Unit 핵심원리 — 문법 Tree

Token 정보를 가공해서 노드들을 만들고, 노드들을 조립하여 "문법 Tree"를 만든다. 이
문법 Tree가 완성되어야만 실행 가능한 구조가 된다.

### Assembly Unit 핵심원리 — 문법 Tree의 구성요소

- **Expression 노드 (표현식, Expr)**: 값을 만드는 것. 실행하면 값 하나로 평가(치환)되는
  코드 단위. 예: Binary Expression(이항연산 `+`), Assign Expression(대입연산 `=`).
- **Statement 노드 (문장, Stmt)**: 값 반환 없이 동작을 수행하는 코드 단위. 예: 선언문
  `var a` (변수 선언), 조건문·반복문 `if`, `for`.

예시 — `if (a > 3) { for(...) { ... } }`:

```
Stmt(if)
├── Expr Binary(>)
│     ├── Expr Variable
│     └── Expr Literal
└── Stmt { }
      └── Stmt(for) ... (생략)
```

### Checker Unit 핵심원리 — 오류 검사

재귀호출로 구현한 DFS 알고리즘을 사용해 각 노드(Stmt, Expr)들을 탐색하며, 코드간의
**의미적인 규칙**을 어겼는지 검사한다:

- 변수 중복 선언인지 (같은 블록 내 중복)
- 선언 시 자기 참조

### Executor Unit 핵심원리 — 실행하기

문법 Tree가 다 만들어지면, 재귀호출로 구현된 DFS 알고리즘을 사용하여 각 Expr와 Stmt를
실행한다.

### Prompt Shell 동작 원리

한 줄 한 줄 입력받을 때마다 3단계 파이프라인(Assembler Unit → Checker Unit →
Executor Unit)이 모두 수행된다.

```
$ python
>>> a = 5
>>> b = 10
>>> print(a + b)
15
```

### [정리] Code Fab 동작

Code Fab은 마치 공장처럼, 한 줄의 프롬프트 입력을 받고 즉시 세 Unit 공정(Assembler,
Check, Executor)을 거쳐 실행하는 하나의 공장으로 비유될 수 있다. 이제 팀만의
프로그래밍 언어를 만들고, Interpreter와 Prompt Shell을 직접 제작하는 프로젝트를
진행한다.

---

## Chapter 2-1. Assembler Unit - Tokenizer

### Assembler Unit 개요

Token 생산과 Expr/Stmt 조립 3단계:

1. Assembler Unit은 프롬프트 쉘에서 사용자 입력으로 소스코드를 받는다.
2. 소스코드로부터 부품(Token)들을 생산한다.
3. 생산된 부품(Token)들을 가공하여 실행할 수 있는 Expr/Stmt로 만든다.

### 부품 생산

주어진 소스코드를 여러 Token으로 분해한다 — 단순 텍스트가 아닌 의미 있는 최소
단위로.

```
var a = 3;  →  VAR_DECL, IDENTIFIER, EQUAL, NUMBER, SEMICOLON
```

### 생산할 부품(Token) 예시

**규격이 정해져 있는 Token**
- 키워드: `if`, `for`, `var` 등
- 연산자: `> < = + - * / ! and or` 등
- 리터럴: `True`, `False`, 숫자 리터럴, 문자열 리터럴 등

**그 외**: identifier(식별자), 세미콜론, 소/중괄호 등

**Token 클래스 예시**

```
class Token {
    TokenType type;
    String origin;
    ...
    Token(TokenType type, String origin, ...) { }
    ...
}
```

→ `TokenType`을 필드로 가지고, 원본 문자열을 따로 기록해둔다. 필요시 다른 정보 추가
가능.

### Tokenizer 예시

**예시 1** — 입력 `age = 37`:

```
[Token(IDENTIFIER, "age"), Token(EQUAL, "="), Token(NUMBER, "37", value=37.0), Token(EOF, "")]
```

절차: 1) 문자 읽기 (예: "age" 읽기) → 2) 문자 패턴 인식 (age를 identifier로 인식) →
3) 토큰화 (Token(IDENTIFIER, ...) 생성) → 토큰 반복 수집.

**예시 2** — 입력 `if ( x > 10 )`:

```
[Token(IF,"if"), Token(LEFT_PAREN,"("), Token(IDENTIFIER,"x"), Token(GREATER,">"),
 Token(NUMBER,"10",value=10.0), Token(RIGHT_PAREN,")"), Token(EOF,"")]
```

**예시 3** — 입력 `a + b * 3`:

```
[Token(IDENTIFIER,"a"), Token(PLUS,"+"), Token(IDENTIFIER,"b"), Token(STAR,"*"),
 Token(NUMBER,"3",value=3.0), Token(EOF,"")]
```

### 구현해야할 Token 예시 정리

| Token Type | 예시 | 비고 |
|---|---|---|
| `LEFT_PAREN`, `RIGHT_PAREN` | `( )` | 그룹핑 |
| `LEFT_BRACE`, `RIGHT_BRACE` | `{ }` | 블록 스코프 |
| `SEMICOLON` | `;` | 구분자 |
| `PLUS`/`MINUS`/`STAR`/`SLASH` | `+ - * /` | 산술연산 |
| `EQUAL` | `=` | 할당 |
| `GREATER`/`LESS` | `> <` | 비교 |
| `IDENTIFIER` | `x, y, z, calcSum` | 식별자 |
| `STRING` | `"hello"` | 문자열 |
| `NUMBER` | `7`, `3.141592` | 숫자 (double) |
| `VAR` | `var` | 변수 선언 |
| `IF` / `ELSE` | `if else` | 조건문 |
| `FOR` | `for` | 반복문 |
| `TRUE` / `FALSE` | `true false` | 불리언 |
| `AND` / `OR` | `and or` | 논리 |
| `PRINT` | `print` | 출력문 |
| `EOF` | | 토큰 스트림 끝 |

이외에 필요한 토큰이 있는 경우 팀에서 추가로 구현 가능.

---

## Chapter 2-2. Assembler Unit - Expression

### 문법 Tree 특징

- Expr는 여러 개의 Expr과 Token을 조합하여 만들어진다.
- Stmt는 여러 개의 Expr, Stmt, Token을 조합하여 만들어진다.
- **Expr 내부에 Stmt를 Child로 갖는 것은 허용하지 않는다.**

### Expr 종류

- **Literal Expression** — Child가 없는 단일 구조. 예: `123` → `Literal Expr(123)`.
- **Variable Expression** — 변수의 이름(식별자)을 나타내는 노드. 예: `a` →
  `Variable Expr(a)`.
- **Boolean Literal Expression** — Child가 없는 단일 구조. 예: `true` →
  `Boolean LiteralExpr(true)`. (Literal 하나로 통합하거나, Boolean/String Literal로
  분리 가능 — 팀 재량)
- **Unary Expression** — 값을 1개만 사용하는 연산자. 종류: `! + -`.
  ```
  -a  →  UnaryExpr(-) → VariableExpr(a)
  !a  →  UnaryExpr(!) → VariableExpr(a)
  ```
- **Assign Expression** — 변수에 값을 대입하는 노드.
  ```
  a = 10  →  AssignExpr(=) [Token(IDENTIFIER,"a"), LiteralExpr(10)]
  a = b   →  AssignExpr(=) [Token(IDENTIFIER,"a"), VariableExpr(b)]
  ```
- **Binary Expression** — 값을 2개 사용하는 연산자. 종류: `+ * >` 등.
  ```
  a + b  →  BinaryExpr(+) [VariableExpr(a), VariableExpr(b)]
  a * b  →  BinaryExpr(*) [VariableExpr(a), VariableExpr(b)]
  a > b  →  BinaryExpr(>) [VariableExpr(a), VariableExpr(b)]
  ```
- **Assign + Binary 조합** — `x = a + b`:
  ```
  AssignExpr(=) [Token(IDENTIFIER,"x"), BinaryExpr(+)[VariableExpr(a), VariableExpr(b)]]
  ```

### 연산 우선순위

우선순위에 맞추어 트리가 구성된다.

`a + b * 3` → 곱셈이 먼저 묶인다:

```
BinaryExpr(+)
├── VariableExpr(a)
└── BinaryExpr(*)
      ├── VariableExpr(b)
      └── LiteralExpr(3)
```

`(a + b) * 3` → 괄호(GroupingExpr)가 우선순위를 바꾼다:

```
BinaryExpr(*)
├── GroupingExpr(괄호)
│     └── BinaryExpr(+) [VariableExpr(a), VariableExpr(b)]
└── LiteralExpr(3)
```

### Expr 예시 정리

Expression의 특징은 실행 시 **평가(evaluate)**가 가능하다는 것.

- 값 생성: `Literal Expr`(리터럴 값 생성), `Variable Expr`(변수 참조)
- 연산: `Binary Expr`(이항연산 `+ - * / < >` 등), `Unary Expr`(단항연산 `- !`),
  `Logical Expr`(논리연산 `and or`), `Grouping Expr`(괄호 `( )`)
- 대입: `Assign Expr`(변수 대입)

| Expr Type | 예시 |
|---|---|
| Literal | `3`, `"hi"`, `true` |
| Variable | `a` (변수) |
| Assign | `a = 3` |
| Binary | `1 + 2`, `a > 0`, `2 * 3` |
| Unary | `-x`, `!isExist` |
| Grouping | `(1 + 2)` |
| Logical | `a and b` |

---

## Chapter 2-3. Assembler Unit - Statement

### 문법 Tree 특징 (복습 + 추가)

- Expr는 여러 개의 Expr과 Token을 조합하여 만들어진다.
- Stmt는 여러 개의 Expr, Stmt, Token을 조합하여 만들어진다.
- Expr 내부에 Stmt를 Child로 갖는 것은 허용하지 않는다.
- **트리의 루트(최상위)는 항상 Stmt이다.**
- **Token은 노드가 아니라 각 노드의 필드로 보관된다.**

### 조립체 생산

Expr은 값을 계산하는 것, Statement는 행동을 수행하는 것.

- `x = 3` → Expression (계산 수행)
- `x = 3;` → Statement (실행 가능한 한 문장)

### IfStmt — `if (x > 0) y = 1;`

```
IfStmt
├── condition: BinaryExpr(>)
│     ├── left: VariableExpr [name: Token(IDENTIFIER,"x")]
│     └── right: LiteralExpr(0.0)
└── thenBranch: ExpressionStmt
      └── AssignExpr [name: Token(IDENTIFIER,"y"), value: LiteralExpr(1.0)]
```

`ExpressionStmt`는 Expr을 감싸는 Stmt(Wrapper)다.

### IfStmt with else — `if (x > 0) y = 1; else y = 2;`

```
IfStmt
├── condition: BinaryExpr(>) [Variable(x), Literal(0.0)]
├── thenBranch: ExpressionStmt [Assign(y, Literal(1.0))]
└── elseBranch: ExpressionStmt [Assign(y, Literal(2.0))]
```

### BlockStmt — `{ x = 1; y = 2; }`

```
BlockStmt
├── ExpressionStmt [Assign(x, Literal(1.0))]
└── ExpressionStmt [Assign(y, Literal(2.0))]
```

### 변수 선언(var) — `var x = 10;`

```
VarDeclareStmt
├── name: Token(IDENTIFIER,"x")
└── initializer: LiteralExpr(10)
```

### 구현해야할 Stmt 정리

| Stmt Type | 예시 |
|---|---|
| Expression | `a + 1;` (Expr을 Stmt으로, Wrapper) |
| Print | `print a;` |
| VarDeclare | `var a = 3;` |
| Block | `{ .... }` |
| If | `if (a > 0) { ...} else { ... }` |
| For | `for(var i = 0; i < 3; i = i + 1){ ... }` |

---

## Chapter 2-4. Assembler Unit — 가공 작업

### 문법 규칙 ←→ 문법 트리

문법 트리는 특정 코드의 문법 규칙이 그대로 적용된 트리다. 예를 들어 if Stmt의 문법
규칙:

```
if Stmt → "if" "(" expression ")" statement ("else" statement)?
```

→ if 문은 `if ( expression ) statement`로 구성되며, 옵션으로 `else statement`가 올 수
있다 (`?`는 옵션이라는 의미).

1. if Stmt의 토큰들은 규칙에 정의된 순서대로 등장한다 (`"if" "(" expression ...`).
2. `"if" "(" ")"`처럼 리터럴 문자열은 반드시 해당 자리에 위치 — 다른 토큰으로 대체
   불가.
3. `expression`, `statement`는 또 다른 규칙이 적용되는 자리이며, 여기서 다른 규칙으로
   확장되기 때문에 문법 트리는 자연스럽게 **재귀 구조**의 트리가 된다.

단, 실행에 불필요한 토큰(`=`, `;` 등)은 노드로 만들지 않는다.

### Parser의 조립 과정 (예: `var a = 3 + 7;`)

문법 규칙에 맞게 Parser가 동작해야 한다. 조립 과정: **토큰들을 하나씩 소비 → 노드
구성 → 트리 구조로 조립**.

1. `var` 토큰 소비 → `VarDeclStmt` 노드 생성 준비 (`name`, `initializer` 필드는 아직
   미결정).
2. `IDENTIFIER("a")` 토큰 소비 → `name` 필드를 채움.
3. `EQUAL` 토큰 소비 → 트리에는 넣지 않는다.
4. `3`을 `LiteralExpr(3)`으로 생성 → 오른쪽 피연산자 유무는 operator가 결정되어야
   알 수 있으므로 우선 `left`에 넣는다 (operator가 없으면 단독 표현식으로 끝).
5. `+` 발견 → 이항 연산자로 인식, `operator`에 `Token(PLUS, "+")` 입력.
6. `7`을 `LiteralExpr(7)`으로 생성 → `right`에 채움.
7. `BinaryExpr` 노드를 생성하고, `VarDeclStmt`의 `initializer`로 연결한다.
8. `SEMICOLON` 발견 시 변수선언문의 parsing을 종료하고 `VarDeclStmt`를 최종 생성한다.

최종 결과:

```
VarDeclStmt
├── name: Token(IDENTIFIER, "a")
└── initializer: BinaryExpr(+)
      ├── left: LiteralExpr(3)
      └── right: LiteralExpr(7)
```

이후 Checker Unit은 이 트리 조립체로 실행 전 오류를 검토하고, Executor Unit은 이를
실제 실행해 결과를 얻는다.

### 문법 검사 (파싱 에러)

토큰화된 부품 조립 과정에서 올바르지 못한 부품인 경우 오류를 발생시킨다.

예: `var a = 3 + ;` (`+` 우항 부분이 빠짐) → 우항 자리에 와야 할 Expr이 없으므로 오류
발생.

### Assembler Unit 요약

**원자재(소스코드) → 부품(Token) → 조립체(Expr/Stmt/Token 문법트리)**

- 원자재인 소스코드를 분석하여 부품들 모음인 Token List를 생성한다.
- Token List를 읽어서 실행 가능한 문법 트리를 완성한다.
- 이후 Executor Unit에서 문법트리를 실행할 수 있게 된다.

```
var a = 3;
  ↓ (토큰화)
[VAR_DECL, IDENTIFIER("a"), EQUAL, NUMBER(3), SEMICOLON]
  ↓ (가공)
VarDeclStmt
├── name: Token(IDENTIFIER,"a")
└── initializer: LiteralExpr(value: 3.0)
```

### Token, Expr, Stmt 정리 (자율성 안내)

- 여기까지 소개한 내용은 **참고용**으로, 필요시 추가·축소·변경 가능하다.
- 문법 규칙의 세부사항, 그리고 각 노드에 필요한 필드는 **팀에서 정한다**.
  - 예: `Binary Expr` 노드는 `left(Expr)`, `right(Expr)`, `operator(Token 또는 enum)`
    필드가 필요하다.
  - 예: `Var Stmt` 노드는 `name(변수 이름 토큰)`, `initializer(Expr, 없을 수 있음)`
    필드가 필요하다.
- 단, 뒤에 주어지는 **테스트용 스크립트를 전부 통과할 수 있어야 한다** (테스트용
  스크립트 문법을 custom 언어에 맞게 변경하는 것은 가능).

---

## Chapter 3. Checker Unit 제작

조립체를 실행하기 전 검수를 한다.

### Checker Unit 오류 검사 개요

- Assembler Unit이 만든 조립체 검수를 통해 소스코드의 오류·경고를 검출한다.
- 문법적 오류는 Assembly Unit에서 이미 수행했으므로, 여기서는 **코드간 의미상
  오류검사**를 한다.
- 이번 챕터에서 구현할 것: **변수 중복 선언 Error 검출**, **지역 변수 초기화 시 자기
  참조 Error 검출**.

### [복습] Checker Unit 핵심원리 — 오류 검사

재귀호출로 구현한 DFS 알고리즘으로 각 노드를 탐색하며, 각 Stmt·Expr이 의미적으로
올바른지 검사한다: 변수 중복 선언(같은 블록 내 중복), 선언 시 자기 참조 등.

### 오류 검사 — 로컬 스코프 중복 선언 오류

Checker Unit은 현재 스코프에 동일한 변수를 선언하면 오류로 처리한다.

```
{
    var a = "first";
    var a = "second";  // Error
}
```

```
> { var a = 10; }
> { var a = 11; var a = 12; }
> [1번째 줄] 'a'에러: 이미 해당 변수는 현재 스코프에서 사용중입니다.
```

### 오류 검사 — 선언 시 자기 참조

초기화되지 않은 상태에서 접근하는 오류를 체크한다.

```
{
    var a = a + 1;  // Error
}
> [2번째 줄] 자신의 초기화식에서 지역변수를 읽을 수 없습니다.
```

---

## Chapter 4. Executor Unit 제작

조립체의 tree 구조를 순회하며 실제로 실행한다.

### Tree 구조 순회하며 실행

Executor Unit은 트리 구조의 Stmt 조립체를 실행한다 — 조립체의 트리 구조를 재귀적으로
평가하며 실제로 실행한다.

### [복습] Executor Unit 핵심원리 - 실행하기

문법 Tree가 다 만들어졌으므로, 재귀호출로 구현된 DFS 알고리즘을 사용하여 각 Expr와
Stmt를 실행한다.

### 실행 예시 1 — `print 3 + 2;`

```
PrintStmt
└── expression: BinaryExpr(+)
      ├── LiteralExpr(3)
      └── LiteralExpr(2)
```

1. PrintStmt → expression 평가 시작
2. Binary(+) → left, right 순서로 평가
3. Literal(3) → 3 반환
4. Literal(2) → 2 반환
5. Binary(+) → 3 + 2 = 5 반환
6. PrintStmt → stdout에 5 출력

### 실행 예시 2 — `if (a > 5) { print 3 + 2; }`

```
IfStmt
├── condition: BinaryExpr(>) [Variable(a), Literal(5)]
└── thenBranch: BlockStmt
      └── PrintStmt [BinaryExpr(+)[Literal(3), Literal(2)]]
```

1. If Stmt → condition 평가 시작
2. Variable(a) → a의 값 반환 (예: 10)
3. Literal(5) → 5 반환
4. Binary(>) → 10 > 5 = true 반환
5. If Stmt → true이므로 thenBranch 진입
6. Block Stmt → 내부 문장 실행 시작
7~10. Print Stmt → Binary(+) 평가 → 3 + 2 = 5
11. Print Stmt → print(5) 출력 완료
12~13. Block Stmt, If Stmt → 실행 완료

### 실행 예시 3 — `if (a > 0) a = 3 + 7 * 5;`

```
IfStmt
├── condition: BinaryExpr(>) [Variable(a), Literal(0)]
└── thenBranch: ExpressionStmt
      └── AssignExpr [name: a, value: BinaryExpr(+)
            ├── Literal(3)
            └── BinaryExpr(*) [Literal(7), Literal(5)]]
```

평가 순서: condition(true) → thenBranch 진입 → `7 * 5 = 35` → `3 + 35 = 38` →
`a = 38` 저장 → 실행 완료.

### Tree 구조 순회 예시 — for문 (`for (var i = 0; i < 3; i = i + 1) { print "#"; }`)

```
ForStmt
├── init: VarStmt [name: i, initializer: Literal(0)]
├── condition: BinaryExpr(<) [Variable(i), Literal(3)]
├── increment: AssignExpr [name: i, value: BinaryExpr(+)[Variable(i), Literal(1)]]
└── body: BlockStmt
      └── PrintStmt [Literal("#")]
```

실행 흐름: 초기화(`i=0` 선언) → 조건 평가(`i<3`) → 참이면 body 진입(`#` 출력) →
increment 실행(`i=i+1`) → 조건이 거짓이 될 때까지 반복 → 종료.

### Tree 구조 순회 예시 — for + if 중첩 (`for (var i=0; i<2; i=i+1) { if(a>3) a = a-1; }`)

for문의 body 안에 IfStmt가 들어있는 구조. 매 반복마다 condition → body(if 평가 →
조건에 따라 `a = a - 1` 실행) → increment 순서로 진행되며, `i`가 종료조건을 만족할
때까지 반복한다.

### 변수 저장소

실행 중 변수의 이름과 값을 저장하고 참조하는 데이터 저장소가 필요하다.

- Executor Unit은 실행하는 동안 변수 저장소를 운용한다.
- **Global 저장소**와 **Local 저장소**로 나뉜다.
- Global 저장소는 전역으로 사용된다.
- Local 저장소는 `{ }` 블록으로 감싼 지역에서 사용된다 (블록이 중첩되면 Local
  저장소도 중첩된다).

### 변수 저장소의 생성과 소멸

블록 `{ }`이 생성될 때마다 새로운 로컬 변수 저장소를 생성하고, 블록 종료 시 소멸한다.

```
var a = 10;      --- global 변수 저장소에 저장
{                --- 해당 로컬 변수 저장소 새로 생성
    var b = 20;  --- 로컬 변수 저장소에 저장
    print a + b; --- a: global에서, b: 로컬 변수 저장소에서 읽기
}                --- 로컬 변수 저장소 소멸
var c = 20;      --- global 변수 저장소에 저장
```

### 여러 개의 로컬 저장소

변수 사용 시, **가장 인접한 저장소부터 상위로 거슬러 올라가며 찾는다**: 현재 저장소 →
상위 저장소 → ... → Global 저장소.

```
var ga = 3;         -- Global 저장소
{
    var a = 2;      -- 저장소 A
    {
        var a = 7;  -- 저장소 B
        {
                        -- 저장소 C
            print a;   // 1: 저장소 C(없음) → 저장소 B(찾음! 7)
            print ga;  // 2: C(없음) → B(없음) → A(없음) → Global(찾음! 3)
        }
        print a;       // 3: 저장소 B(찾음! 7)
    }
}
```

### Runtime 오류 보고

Executor Unit은 실행 중 다음 Runtime 오류들을 처리한다: **타입 불일치**, **정의되지
않은 변수 참조**, **0으로 나누기**.

**타입 불일치**

피연산자 타입 오류 예: `true * false` (Boolean에 `*` 연산 불가), `3 - "hello"` (숫자 -
문자열 불가). 문제 상황을 명시해서 오류를 보고한다.

```
3 – "hello"
> [1번째줄] 피연산자는 반드시 숫자여야 한다.
```

**정의되지 않은 변수 참조**

선언된 적이 없는 변수를 참조하면 에러.

```
x = 5;   // 선언 없이 사용
> [1번째줄] 미정의된 변수 'x'
```

**0으로 나누는 동작 에러**

나눗셈 식에서 제수(Divisor)가 0인 경우 런타임 오류.

```
a = 3 / 0;
> [1번째줄] 0으로 나눈 오류
```

---

## Chapter 5. 테스트용 스크립트

다음 링크에서 제공되는 예시 스크립트를 통과하도록 구현한다. 단, 스크립트에 등장하는
**기능과 동작은 유지**한 채로 **언어 문법은 변경 가능**하다.

- 참고 Gist: `https://gist.github.com/aijeonghwan-star/d1535e870aeb6a4a928142d4d57c191e`

---

## Chapter 6. 팀 프로젝트 진행

### 프로젝트 준비

- 창의력 있는 팀 이름을 정한다.
- 팀에서 사용할 코딩 규칙(코드 컨벤션, 코딩 스탠다드 및 룰)을 설정한다.
- 팀장과 팀원의 역할을 분배한다.

### [1~2일차] 요청사항

**Claude Code 사용**: 개발 및 협업에 사용 가능. 단, 빠른 코드 생성이 가능하더라도
생성된 코드의 **이해 없이, 검토 없이 넘어가면 안 된다**.

**TDD 개발 필수**
- 1일차~2일차: TDD 개발이 포함되어야 한다.
- 3일차~4일차: TDD 없이 개발해도 된다. Unit Test + 리팩토링만 해도 된다.

### [3~4일차] 기능 추가 개발 및 리팩토링

3일차에는 기능 추가 요청이 있을 예정이다 (function 관련 기능, 정적 배열 구현, 실행전
최적화 등). 기능 추가에 대비하여 1~2일차까지 클린한 코드를 만들어두어야 하며, 새로운
기능 추가에 대응하기 좋은 디자인 패턴·설계가 필요하다.

### [5일차] 발표 준비 및 발표

- 오전: PPT 준비 / 오후: 발표 및 마무리. 팀장이 발표(변경 가능).
- 발표 자료에는 **리팩토링 전후 결과**와 **코드리뷰 활동 캡쳐**가 포함되어야 한다.
- 클린코드를 신경 쓰지 않는 코드를 먼저 만들고 리팩토링으로 점차 개선하는 방식을
  권장하며, 리팩토링 전후 비교를 캡쳐할 수 있도록 **리팩토링 과정마다 Commit**을
  권장한다.

### CodeFab Interpreter 프로젝트 시작

프로젝트 진행/기능 구현에 대한 질문은 프로젝트 코치/강사에게 언제든 질문한다.
