import pytest

from codefab.assembler.assembler import Assembler
from codefab.checker import Checker
from codefab.error import (
    DuplicateImportError,
    DuplicateVariableError,
    ImportedFileNotFoundError,
    ImportInsideLoopError,
    InvalidModuleContentError,
    SelfReferenceInInitializerError,
)
from codefab.module_loader import ModuleLoader
from codefab.tokens import Token, TokenType


def make_token(lexeme, line=1):
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


@pytest.fixture
def stub_module_loader(mocker):
    # 스코프/루프 규칙만 검증하는 테스트가 실제 파일 시스템에 의존하지 않도록
    # ModuleLoader를 대역으로 대체한다.
    loader = mocker.Mock()
    loader.resolve.side_effect = lambda literal: literal
    loader.load.return_value = []
    return loader


@pytest.fixture
def sut(stub_module_loader):
    return Checker(module_loader=stub_module_loader)


@pytest.fixture
def make_variable(mocker):
    def _make(lexeme, line=1):
        variable = mocker.Mock()
        variable.name = make_token(lexeme, line)
        variable.accept.side_effect = lambda visitor: visitor.visit_variable(variable)
        return variable

    return _make


@pytest.fixture
def make_var_stmt(mocker):
    def _make(lexeme, initializer=None, line=1):
        var_stmt = mocker.Mock(initializer=initializer)
        var_stmt.name = make_token(lexeme, line)
        var_stmt.accept.side_effect = lambda visitor: visitor.visit_var_stmt(var_stmt)
        return var_stmt

    return _make


@pytest.fixture
def make_exp_stmt(mocker):
    def _make(expression):
        exp_stmt = mocker.Mock(expression=expression)
        exp_stmt.accept.side_effect = lambda visitor: visitor.visit_expression_stmt(
            exp_stmt
        )
        return exp_stmt

    return _make


@pytest.fixture
def make_binary(mocker):
    def _make(left, right):
        binary = mocker.Mock(left=left, right=right)
        binary.accept.side_effect = lambda visitor: visitor.visit_binary(binary)
        return binary

    return _make


@pytest.fixture
def make_block_stmt(mocker):
    def _make(statements):
        block_stmt = mocker.Mock(statements=statements)
        block_stmt.accept.side_effect = lambda visitor: visitor.visit_block_stmt(
            block_stmt
        )
        return block_stmt

    return _make


@pytest.fixture
def make_literal(mocker):
    def _make(value):
        literal = mocker.Mock(value=value)
        literal.accept.side_effect = lambda visitor: visitor.visit_literal(literal)
        return literal

    return _make


@pytest.fixture
def make_grouping(mocker):
    def _make(expression):
        grouping = mocker.Mock(expression=expression)
        grouping.accept.side_effect = lambda visitor: visitor.visit_grouping(grouping)
        return grouping

    return _make


@pytest.fixture
def make_unary(mocker):
    def _make(right):
        unary = mocker.Mock(right=right)
        unary.accept.side_effect = lambda visitor: visitor.visit_unary(unary)
        return unary

    return _make


@pytest.fixture
def make_logical(mocker):
    def _make(left, right):
        logical = mocker.Mock(left=left, right=right)
        logical.accept.side_effect = lambda visitor: visitor.visit_logical(logical)
        return logical

    return _make


@pytest.fixture
def make_assign(mocker):
    def _make(lexeme, value, line=1):
        assign = mocker.Mock(value=value)
        assign.name = make_token(lexeme, line)
        assign.accept.side_effect = lambda visitor: visitor.visit_assign(assign)
        return assign

    return _make


@pytest.fixture
def make_print_stmt(mocker):
    def _make(expression):
        print_stmt = mocker.Mock(expression=expression)
        print_stmt.accept.side_effect = lambda visitor: visitor.visit_print_stmt(
            print_stmt
        )
        return print_stmt

    return _make


@pytest.fixture
def make_if_stmt(mocker):
    def _make(condition, then_branch, else_branch=None):
        if_stmt = mocker.Mock(
            condition=condition, then_branch=then_branch, else_branch=else_branch
        )
        if_stmt.accept.side_effect = lambda visitor: visitor.visit_if_stmt(if_stmt)
        return if_stmt

    return _make


@pytest.fixture
def make_for_stmt(mocker):
    def _make(initializer, condition, increment, body):
        for_stmt = mocker.Mock(
            initializer=initializer,
            condition=condition,
            increment=increment,
            body=body,
        )
        for_stmt.accept.side_effect = lambda visitor: visitor.visit_for_stmt(for_stmt)
        return for_stmt

    return _make


@pytest.fixture
def make_import_stmt(mocker):
    def _make(path_literal, alias_lexeme, line=1):
        import_stmt = mocker.Mock()
        import_stmt.path = Token(
            type=TokenType.STRING,
            lexeme=f'"{path_literal}"',
            literal=path_literal,
            line=line,
        )
        import_stmt.alias = make_token(alias_lexeme, line)
        import_stmt.accept.side_effect = lambda visitor: visitor.visit_import_stmt(
            import_stmt
        )
        return import_stmt

    return _make


def test_정상_입력_확인(sut, make_var_stmt, make_variable, make_exp_stmt):
    # arrange
    var_stmt_a = make_var_stmt("a", line=1)
    variable_a = make_variable("a", line=2)
    exp_statement = make_exp_stmt(variable_a)

    ast = [var_stmt_a, exp_statement]

    # act
    sut.resolve(ast)

    # assert
    assert sut.declared == {"a"}


def test_변수_중복_선언_에러_검출(sut, make_var_stmt, make_block_stmt):
    # arrange
    var_stmt_a1 = make_var_stmt("a", line=1)
    var_stmt_a2 = make_var_stmt("a", line=2)
    block_stmt = make_block_stmt([var_stmt_a1, var_stmt_a2])

    ast = [block_stmt]

    # act
    # assert
    with pytest.raises(DuplicateVariableError, match="이미 선언된 변수입니다."):
        sut.resolve(ast)


def test_다른_스코프에서는_변수_재선언_허용(sut, make_var_stmt, make_block_stmt):
    # arrange
    var_stmt_outer = make_var_stmt("a", line=1)
    var_stmt_inner = make_var_stmt("a", line=2)
    block_stmt = make_block_stmt([var_stmt_inner])

    ast = [var_stmt_outer, block_stmt]

    # act
    sut.resolve(ast)

    # assert
    assert sut.declared == {"a"}


def test_지역_변수_초기화_시_자기_참조_에러_검출(
    sut, make_variable, make_var_stmt, make_block_stmt
):
    # arrange
    variable_a = make_variable("a")
    var_stmt_a = make_var_stmt("a", initializer=variable_a)
    block_stmt = make_block_stmt([var_stmt_a])

    ast = [block_stmt]

    # act
    # assert
    with pytest.raises(
        SelfReferenceInInitializerError, match="지역 변수 자기 참조 에러입니다."
    ):
        sut.resolve(ast)


def test_리터럴은_에러_없이_방문된다(sut, make_literal, make_exp_stmt):
    # arrange
    literal = make_literal(1.0)
    exp_statement = make_exp_stmt(literal)

    ast = [exp_statement]

    # act
    sut.resolve(ast)

    # assert
    literal.accept.assert_called_once_with(sut)


def test_그룹핑은_내부_표현식을_방문한다(
    sut, make_grouping, make_variable, make_exp_stmt
):
    # arrange
    variable_a = make_variable("a")
    grouping = make_grouping(variable_a)
    exp_statement = make_exp_stmt(grouping)

    ast = [exp_statement]

    # act
    sut.resolve(ast)

    # assert
    variable_a.accept.assert_called_once_with(sut)


def test_단항_표현식은_피연산자를_방문한다(
    sut, make_unary, make_variable, make_exp_stmt
):
    # arrange
    variable_a = make_variable("a")
    unary = make_unary(variable_a)
    exp_statement = make_exp_stmt(unary)

    ast = [exp_statement]

    # act
    sut.resolve(ast)

    # assert
    variable_a.accept.assert_called_once_with(sut)


def test_논리_표현식은_좌우_피연산자를_방문한다(
    sut, make_logical, make_variable, make_exp_stmt
):
    # arrange
    variable_a = make_variable("a")
    variable_b = make_variable("b")
    logical = make_logical(variable_a, variable_b)
    exp_statement = make_exp_stmt(logical)

    ast = [exp_statement]

    # act
    sut.resolve(ast)

    # assert
    variable_a.accept.assert_called_once_with(sut)
    variable_b.accept.assert_called_once_with(sut)


def test_대입_표현식은_값을_방문한다(
    sut, make_var_stmt, make_assign, make_variable, make_exp_stmt
):
    # arrange
    var_stmt_a = make_var_stmt("a", line=1)
    variable_b = make_variable("b")
    assign = make_assign("a", variable_b, line=2)
    exp_statement = make_exp_stmt(assign)

    ast = [var_stmt_a, exp_statement]

    # act
    sut.resolve(ast)

    # assert
    variable_b.accept.assert_called_once_with(sut)


def test_출력문은_표현식을_방문한다(sut, make_print_stmt, make_variable):
    # arrange
    variable_a = make_variable("a")
    print_stmt = make_print_stmt(variable_a)

    ast = [print_stmt]

    # act
    sut.resolve(ast)

    # assert
    variable_a.accept.assert_called_once_with(sut)


def test_조건문은_조건식과_분기를_방문한다(
    sut, make_if_stmt, make_variable, make_exp_stmt
):
    # arrange
    variable_a = make_variable("a")
    condition = make_variable("condition")
    then_branch = make_exp_stmt(variable_a)
    if_stmt = make_if_stmt(condition, then_branch)

    ast = [if_stmt]

    # act
    sut.resolve(ast)

    # assert
    condition.accept.assert_called_once_with(sut)
    then_branch.accept.assert_called_once_with(sut)


def test_조건문은_else_분기도_방문한다(
    sut, make_if_stmt, make_var_stmt, make_variable, make_exp_stmt
):
    # arrange
    variable_b = make_variable("b")
    else_branch = make_exp_stmt(variable_b)
    if_stmt = make_if_stmt(
        make_variable("condition"),
        make_exp_stmt(make_variable("a")),
        else_branch=else_branch,
    )

    ast = [if_stmt]

    # act
    sut.resolve(ast)

    # assert
    else_branch.accept.assert_called_once_with(sut)


def test_반복문은_초기화식_조건식_증감식_본문을_방문한다(
    sut, make_for_stmt, make_var_stmt, make_variable, make_exp_stmt
):
    # arrange
    initializer = make_var_stmt("i", line=1)
    condition = make_variable("i", line=2)
    increment = make_variable("i", line=3)
    body = make_exp_stmt(make_variable("a", line=4))
    for_stmt = make_for_stmt(initializer, condition, increment, body)

    ast = [for_stmt]

    # act
    sut.resolve(ast)

    # assert
    initializer.accept.assert_called_once_with(sut)
    condition.accept.assert_called_once_with(sut)
    increment.accept.assert_called_once_with(sut)
    body.accept.assert_called_once_with(sut)


def test_가져오기_문은_별칭을_현재_스코프에_등록한다(sut, make_import_stmt):
    # arrange
    import_stmt = make_import_stmt("sum.txt", "sum")

    ast = [import_stmt]

    # act
    sut.resolve(ast)

    # assert
    assert sut.declared == {"sum"}


def test_같은_스코프에서_별칭_이름_중복시_에러(sut, make_import_stmt, make_block_stmt):
    # arrange
    import_a = make_import_stmt("a.txt", "sum", line=1)
    import_b = make_import_stmt("b.txt", "sum", line=2)
    block_stmt = make_block_stmt([import_a, import_b])

    ast = [block_stmt]

    # act
    # assert
    with pytest.raises(DuplicateVariableError, match="이미 선언된 변수입니다."):
        sut.resolve(ast)


def test_다른_스코프에서는_같은_별칭_이름_재선언_허용(
    sut, make_import_stmt, make_block_stmt
):
    # arrange
    import_outer = make_import_stmt("a.txt", "sum", line=1)
    import_inner = make_import_stmt("b.txt", "sum", line=2)
    block_stmt = make_block_stmt([import_inner])

    ast = [import_outer, block_stmt]

    # act
    sut.resolve(ast)

    # assert
    assert sut.declared == {"sum"}


def test_반복문_내에선_가져오기_사용시_에러(
    sut, make_for_stmt, make_var_stmt, make_variable, make_import_stmt
):
    # arrange
    initializer = make_var_stmt("i", line=1)
    condition = make_variable("i", line=1)
    increment = make_variable("i", line=1)
    body = make_import_stmt("sum.txt", "sum", line=2)
    for_stmt = make_for_stmt(initializer, condition, increment, body)

    ast = [for_stmt]

    # act
    # assert
    with pytest.raises(
        ImportInsideLoopError, match="반복문 내부에서는 가져오기를 사용할 수 없습니다."
    ):
        sut.resolve(ast)


def test_반복문_밖에서는_가져오기_사용_가능(
    sut, make_for_stmt, make_var_stmt, make_variable, make_import_stmt, make_block_stmt
):
    # arrange
    initializer = make_var_stmt("i", line=1)
    condition = make_variable("i", line=1)
    increment = make_variable("i", line=1)
    body = make_block_stmt([])
    for_stmt = make_for_stmt(initializer, condition, increment, body)
    import_after_loop = make_import_stmt("sum.txt", "sum", line=5)

    ast = [for_stmt, import_after_loop]

    # act
    sut.resolve(ast)

    # assert
    assert sut.declared == {"i", "sum"}


def test_같은_스코프에서_같은_파일_재_import시_에러(
    sut, make_import_stmt, make_block_stmt
):
    # arrange
    import_a = make_import_stmt("sum.txt", "sum", line=1)
    import_b = make_import_stmt("sum.txt", "s2", line=2)
    block_stmt = make_block_stmt([import_a, import_b])

    ast = [block_stmt]

    # act
    # assert
    with pytest.raises(DuplicateImportError):
        sut.resolve(ast)


def test_중첩_스코프에서_상위에서_이미_import된_파일_재_import시_에러(
    sut, make_import_stmt, make_block_stmt
):
    # arrange
    import_outer = make_import_stmt("sum.txt", "sum", line=1)
    import_inner = make_import_stmt("sum.txt", "s2", line=2)
    block_stmt = make_block_stmt([import_inner])

    ast = [import_outer, block_stmt]

    # act
    # assert
    with pytest.raises(DuplicateImportError):
        sut.resolve(ast)


def test_서로_다른_형제_스코프에서는_같은_파일_재_import_허용(
    sut, make_import_stmt, make_block_stmt
):
    # arrange
    block_a = make_block_stmt([make_import_stmt("sum.txt", "sum", line=1)])
    block_b = make_block_stmt([make_import_stmt("sum.txt", "sum", line=2)])

    ast = [block_a, block_b]

    # act
    # assert (에러 없이 통과)
    sut.resolve(ast)


def test_중첩_블록이_끝난_후에는_같은_파일_재_import_허용(
    sut, make_import_stmt, make_block_stmt
):
    # arrange
    block_stmt = make_block_stmt([make_import_stmt("sum.txt", "sum", line=1)])
    import_after_block = make_import_stmt("sum.txt", "sum", line=2)

    ast = [block_stmt, import_after_block]

    # act
    sut.resolve(ast)

    # assert
    assert sut.declared == {"sum"}


def test_실제_모듈로더로_존재하지_않는_파일_가져오기는_에러(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    statements = Assembler().assemble('가져오기 "missing.txt" 별칭 m;')

    with pytest.raises(ImportedFileNotFoundError):
        Checker(module_loader=ModuleLoader()).resolve(statements)


def test_실제_모듈로더로_선언_외_구문이_있는_파일_가져오기는_에러(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad.txt").write_text("출력 1;", encoding="utf-8")
    statements = Assembler().assemble('가져오기 "bad.txt" 별칭 bad;')

    with pytest.raises(InvalidModuleContentError):
        Checker(module_loader=ModuleLoader()).resolve(statements)


def test_실제_모듈로더로_변수_선언만_있는_파일_가져오기는_정상_동작(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "sum.txt").write_text("변수 x = 3;", encoding="utf-8")
    statements = Assembler().assemble('가져오기 "sum.txt" 별칭 sum;')

    checker = Checker(module_loader=ModuleLoader())
    checker.resolve(statements)

    assert checker.declared == {"sum"}
