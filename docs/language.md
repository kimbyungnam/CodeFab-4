# Laugh Language — Assembler Unit 데이터 모델

CodeFab Interpreter는 `Assembler Unit → Checker Unit → Executor Unit` 3단계로
소스 코드를 처리한다. 이 문서는 그중 **Assembler Unit**(원본 문자열을 Token으로
쪼개고, Token을 다시 AST(`Expr` / `Stmt`)로 조립하는 단계)이 다루는 데이터
구조만을 정의한다.

`Checker Unit`(정적 검사)과 `Executor Unit`(실행)이 이 노드들을 어떻게
순회·평가하는지는 이 문서의 범위 밖이며, 별도 문서에서 다룬다. 그래서 아래의
`Expr` / `Stmt` 클래스들은 **순수 데이터 구조**로만 정의하고, `evaluate` /
`execute` 같은 동작 메서드는 포함하지 않는다.

## 1. Lexical 계층 — Token

### TokenType

```python
class TokenType(Enum):
    # 구분자 / 그룹핑
    LEFT_PAREN = auto(); RIGHT_PAREN = auto()
    LEFT_BRACE = auto(); RIGHT_BRACE = auto()
    LEFT_BRACKET = auto(); RIGHT_BRACKET = auto()
    SEMICOLON = auto()

    # 연산자
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto()
    EQUAL = auto(); EQUAL_EQUAL = auto()
    GREATER = auto(); GREATER_EQUAL = auto()
    LESS = auto(); LESS_EQUAL = auto()

    # 리터럴 / 식별자
    IDENTIFIER = auto(); STRING = auto(); NUMBER = auto()

    # 키워드
    VAR = auto(); IF = auto(); ELSE = auto(); FOR = auto()
    TRUE = auto(); FALSE = auto(); AND = auto(); OR = auto()
    PRINT = auto(); ARRAY = auto()

    EOF = auto()
```

| 분류 | TokenType | 예시 |
|---|---|---|
| 구분자 | `LEFT_PAREN` `RIGHT_PAREN` | `(` `)` |
| | `LEFT_BRACE` `RIGHT_BRACE` | `{` `}` |
| | `LEFT_BRACKET` `RIGHT_BRACKET` | `[` `]` |
| | `SEMICOLON` | `;` |
| 산술 연산자 | `PLUS` `MINUS` `STAR` `SLASH` | `+` `-` `*` `/` |
| 대입/동등 | `EQUAL` `EQUAL_EQUAL` | `=` `==` |
| 비교 | `GREATER` `GREATER_EQUAL` `LESS` `LESS_EQUAL` | `>` `>=` `<` `<=` |
| 리터럴 | `IDENTIFIER` `STRING` `NUMBER` | `age` `"hello"` `3.14` |
| 키워드 | `VAR` `IF` `ELSE` `FOR` `TRUE` `FALSE` `AND` `OR` `PRINT` `ARRAY` | `변수` `만약` `아니면` `반복` `참` `거짓` `그리고` `또는` `출력` `배열` |
| 종료 | `EOF` | (입력 끝) |

> `ARRAY`는 정적 배열 리터럴 `Array(n)` / `배열(n)` 을 위한 키워드 토큰이다.
> `if`/`var` 등 다른 키워드와 동일하게 `KEYWORDS` 테이블(`tokenizer.py`)을 통해
> 인식되며, `IDENTIFIER`로 먼저 읽은 뒤 파서에서 이름을 비교하는 방식이 아니다
> — 토큰화 단계에서 확정된다.

> `!` (BANG) / `!=` (BANG_EQUAL)은 현재 범위에서 제외한다. 부정 연산과
> 부등 비교가 필요해지면 `TokenType`에 다시 추가한다.
>
> **키워드는 한글, 나머지는 그대로.** `TokenType` 멤버 이름(`VAR`, `IF`, ...)과
> 연산자 기호(`+` `-` `<` `==` 등), 식별자(`a`, `count`, `outer`처럼 사용자가
> 짓는 이름)는 바뀌지 않는다. 오직 예약어의 **표면 문자열(lexeme)** 만 한글로
> 바뀐다 — 즉 Lexer가 `"변수"`라는 문자열을 보면 `Token(VAR, "변수", None, line)`
> 을 만든다. `TokenType` enum 자체를 한글로 리네이밍하지 않는 이유는, 이 값은
> 코드 내부 식별자일 뿐 소스 코드에 노출되는 표면 문법과 무관하기 때문이다.

### Token

```python
@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str        # 원본 문자열
    literal: Any        # 실제 값 (NUMBER→float, STRING→str, 그 외 None)
    line: int           # 오류 리포팅용 라인 번호
```

**예시**: `age = 37`

```python
[
    Token(IDENTIFIER, "age", None, 1),
    Token(EQUAL, "=", None, 1),
    Token(NUMBER, "37", 37.0, 1),
    Token(EOF, "", None, 1),
]
```

## 2. AST 계층 — Expr / Stmt

`Expr`는 **값으로 평가되는** 노드, `Stmt`는 **부수효과를 일으키는 실행 단위**다.
`Stmt`는 자식으로 `Expr`, `Stmt`, `Token`을 가질 수 있지만 `Expr`는 `Expr`와
`Token`만 자식으로 가진다 (`Expr` 안에 `Stmt`가 들어가는 일은 없다).

```python
class Expr:
    """모든 표현식 노드의 마커 베이스 클래스. 필드 없음."""

class Stmt:
    """모든 문장 노드의 마커 베이스 클래스. 필드 없음."""
```

### 2.1 Expr 계열

| 클래스 | 필드 | 문법 예시 |
|---|---|---|
| `Literal` | `value: object` | `3`, `"hi"`, `참` |
| `Variable` | `name: Token` | `a` |
| `Assign` | `name: Token`, `value: Expr` | `a = 3` |
| `Binary` | `left: Expr`, `operator: Token`, `right: Expr` | `a + b`, `a > b` |
| `Unary` | `operator: Token`, `right: Expr` | `-a` |
| `Logical` | `left: Expr`, `operator: Token`, `right: Expr` | `a 그리고 b` |
| `Grouping` | `expression: Expr` | `(a + b)` |

```python
@dataclass(frozen=True)
class Literal(Expr):
    value: object

@dataclass(frozen=True)
class Variable(Expr):
    name: Token

@dataclass(frozen=True)
class Assign(Expr):
    name: Token
    value: Expr

@dataclass(frozen=True)
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

@dataclass(frozen=True)
class Unary(Expr):
    operator: Token
    right: Expr

@dataclass(frozen=True)
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr

@dataclass(frozen=True)
class Grouping(Expr):
    expression: Expr
```

`Binary`와 `Logical`이 필드 구성은 동일하지만 클래스를 분리하는 이유는,
`그리고`/`또는`은 단축 평가(short-circuit) 대상이라 `Executor Unit`에서 산술/비교
연산과 다른 방식으로 처리되어야 하기 때문이다 (이 구분 자체가 Assembler
단계의 조립 결과이므로 여기서 타입으로 확정해 둔다).

**예시 — `a + b * 3`**

```python
Binary(
    left=Variable(Token(IDENTIFIER, "a", None, 1)),
    operator=Token(PLUS, "+", None, 1),
    right=Binary(
        left=Variable(Token(IDENTIFIER, "b", None, 1)),
        operator=Token(STAR, "*", None, 1),
        right=Literal(3.0),
    ),
)
```

우선순위(`*`가 `+`보다 먼저 묶임)와 결합 방향은 Parser가 만드는 트리 모양으로
표현되며, 이 문서의 데이터 구조 자체에는 우선순위 정보가 없다.

### 2.1.1 정적 배열 확장 Expr (`codefab/array_nodes.py`)

정적 배열 관련 노드는 위의 `Expr` 계열과 같은 규약(`accept(visitor)`)을 따르되,
기존 `ast_nodes.py`는 건드리지 않고 별도 모듈에 정의한다.

| 클래스 | 필드 | 문법 예시 |
|---|---|---|
| `ArrayLiteral` | `size: Expr`, `line: int` | `Array(3)`, `배열(3)` |
| `IndexGet` | `target: Expr`, `index: Expr`, `line: int` | `arr[0]` |
| `IndexSet` | `target: Expr`, `index: Expr`, `value: Expr`, `line: int` | `arr[0] = 10` |

`line`은 `Grouping` 등 기존 노드에는 없던 필드인데, 배열은 실행 중 발생 가능한
런타임 에러(크기/인덱스 타입 오류, 범위 초과 등)를 보고할 때 별도로 참조할
Token이 없어서(예: `ArrayLiteral`은 여는 `(` 하나만 소비) 노드 자체에 라인
번호를 직접 들고 있는다.

### 2.2 Stmt 계열

| 클래스 | 필드 | 문법 예시 |
|---|---|---|
| `ExpressionStmt` | `expression: Expr` | `a + 1;` |
| `PrintStmt` | `expression: Expr` | `출력 a;` |
| `VarDeclareStmt` | `name: Token`, `initializer: Expr \| None` | `변수 a = 3;` |
| `BlockStmt` | `statements: list[Stmt]` | `{ ... }` |
| `IfStmt` | `condition: Expr`, `then_branch: Stmt`, `else_branch: Stmt \| None` | `만약 (a > 0) {...} 아니면 {...}` |
| `ForStmt` | `initializer: Stmt \| None`, `condition: Expr \| None`, `increment: Expr \| None`, `body: Stmt` | `반복 (변수 i=0; i<3; i=i+1) {...}` |

```python
@dataclass(frozen=True)
class ExpressionStmt(Stmt):
    expression: Expr

@dataclass(frozen=True)
class PrintStmt(Stmt):
    expression: Expr

@dataclass(frozen=True)
class VarDeclareStmt(Stmt):
    name: Token
    initializer: Expr | None

@dataclass(frozen=True)
class BlockStmt(Stmt):
    statements: list[Stmt]

@dataclass(frozen=True)
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None

@dataclass(frozen=True)
class ForStmt(Stmt):
    initializer: Stmt | None
    condition: Expr | None
    increment: Expr | None
    body: Stmt
```

`ExpressionStmt`는 `Expr`를 문장 자리에 놓기 위한 래퍼(wrapper)다. 예를 들어
`x = 3;`은 `Assign` 하나로 값을 만들 수 있지만, 세미콜론으로 끝나는 독립된
문장이 되려면 `ExpressionStmt(Assign(...))`처럼 한 번 감싸야 한다.

`initializer` / `condition` / `else_branch`가 `None`을 허용하는 것은 각각
`변수 a;`(초기값 생략), `반복(;;)`(조건 생략), `만약` 단독(`아니면` 없음)을
표현하기 위함이다.

**예시 — `만약 (x > 0) y = 1; 아니면 y = 2;`**

```python
IfStmt(
    condition=Binary(
        left=Variable(Token(IDENTIFIER, "x", None, 1)),
        operator=Token(GREATER, ">", None, 1),
        right=Literal(0.0),
    ),
    then_branch=ExpressionStmt(
        Assign(Token(IDENTIFIER, "y", None, 1), Literal(1.0))
    ),
    else_branch=ExpressionStmt(
        Assign(Token(IDENTIFIER, "y", None, 1), Literal(2.0))
    ),
)
```

**예시 — `반복 (변수 i = 0; i < 3; i = i + 1) { 출력 "#"; }`**

```python
ForStmt(
    initializer=VarDeclareStmt(Token(IDENTIFIER, "i", None, 1), Literal(0.0)),
    condition=Binary(
        left=Variable(Token(IDENTIFIER, "i", None, 1)),
        operator=Token(LESS, "<", None, 1),
        right=Literal(3.0),
    ),
    increment=Assign(
        Token(IDENTIFIER, "i", None, 1),
        Binary(
            left=Variable(Token(IDENTIFIER, "i", None, 1)),
            operator=Token(PLUS, "+", None, 1),
            right=Literal(1.0),
        ),
    ),
    body=BlockStmt([PrintStmt(Literal("#"))]),
)
```

## 3. 문법 정의 (EBNF)

Parser가 위 노드들을 어떤 문법 규칙에서 만들어내는지는 다음과 같다
(우선순위가 낮은 규칙이 위, 높은 규칙이 아래).

```
program     -> statement* EOF ;

statement   -> exprStmt | printStmt | varDecl | block | ifStmt | forStmt ;

exprStmt    -> expression ";" ;
printStmt   -> "출력" expression ";" ;
varDecl     -> "변수" IDENTIFIER ( "=" expression )? ";" ;
block       -> "{" statement* "}" ;
ifStmt      -> "만약" "(" expression ")" statement ( "아니면" statement )? ;
forStmt     -> "반복" "(" ( varDecl | exprStmt | ";" )
                         expression? ";"
                         expression? ")" statement ;

expression  -> assignment ;
assignment  -> ( IDENTIFIER | indexAccess ) "=" assignment | logic_or ;
logic_or    -> logic_and ( "또는" logic_and )* ;
logic_and   -> equality ( "그리고" equality )* ;
equality    -> comparison ( "==" comparison )* ;
comparison  -> term ( ( ">" | ">=" | "<" | "<=" ) term )* ;
term        -> factor ( ( "+" | "-" ) factor )* ;
factor      -> unary ( ( "*" | "/" ) unary )* ;
unary       -> "-" unary | indexAccess ;
indexAccess -> primary ( "[" expression "]" )* ;
primary     -> NUMBER | STRING | "참" | "거짓" | IDENTIFIER
             | arrayLiteral
             | "(" expression ")" ;
arrayLiteral -> ( "Array" | "배열" ) "(" expression ")" ;
```

`indexAccess`는 `primary` 뒤에 `[expression]`이 0개 이상 붙는 후위(postfix)
표현이다 (`arr[0]`, `arr[i][j]`처럼 중첩도 가능). `assignment`는 좌변이
`IDENTIFIER`(→ `Assign`)이거나 `indexAccess`의 결과가 `IndexGet`(→ `IndexSet`
으로 변환)인 경우만 대입 대상으로 허용하고, 그 외에는 파싱 에러를 낸다.

키워드(`"출력"`, `"변수"`, `"만약"`, `"아니면"`, `"반복"`, `"그리고"`, `"또는"`,
`"참"`, `"거짓"`, `"배열"`)만 한글 표면형이고, `NUMBER` / `STRING` / `IDENTIFIER`가
가리키는 실제 값(예: `a`, `count`, `"안녕"`)의 표기법은 그대로다. `"Array"`는
영문 표면형으로도 동일하게 지원한다.

각 규칙과 노드의 대응 관계:

| 문법 규칙 | 대응 노드 |
|---|---|
| `assignment` (대입일 때, 좌변이 `IDENTIFIER`) | `Assign` |
| `assignment` (대입일 때, 좌변이 `indexAccess`) | `IndexSet` |
| `logic_or` / `logic_and` | `Logical` |
| `equality` / `comparison` / `term` / `factor` | `Binary` |
| `unary` | `Unary` |
| `indexAccess` (`[expression]`이 붙을 때) | `IndexGet` |
| `primary` → `NUMBER`/`STRING`/`참`/`거짓` | `Literal` |
| `primary` → `IDENTIFIER` | `Variable` |
| `primary` → `arrayLiteral` | `ArrayLiteral` |
| `primary` → `"(" expression ")"` | `Grouping` |
| `exprStmt` | `ExpressionStmt` |
| `printStmt` | `PrintStmt` |
| `varDecl` | `VarDeclareStmt` |
| `block` | `BlockStmt` |
| `ifStmt` | `IfStmt` |
| `forStmt` | `ForStmt` |

## 4. 범위 경계

- **이 문서가 정의하는 것**: `TokenType`, `Token`, `Expr`/`Stmt` 및 그 하위
  클래스의 필드 구성. Parser가 이 노드들을 어떤 문법 규칙으로 조립하는지.
- **이 문서가 정의하지 않는 것**: `Lexer`/`Parser` 클래스 자체의 메서드
  시그니처, 노드 순회(evaluate/execute) 방식, 스코프(Environment) 구조,
  타입/0-division 등 런타임 에러 처리 — 이들은 Checker Unit / Executor Unit
  문서에서 다룬다.
