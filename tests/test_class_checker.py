import pytest

from codefab.assembler.assembler import Assembler
from codefab.checker import Checker
from codefab.error import (
    ReturnInInitializerError,
    SelfInheritanceError,
    SuperOutsideClassError,
    SuperWithoutSuperclassError,
    ThisOutsideClassError,
)


def resolve(source: str):
    statements = Assembler().assemble(source)
    Checker().resolve(statements)


def test_클래스_선언과_인스턴스_생성은_정상_통과한다():
    resolve(
        """
        클래스 Robot { }
        변수 robot = Robot();
        """
    )


def test_메서드_내부에서_나를_사용하는_것은_정상_통과한다():
    resolve(
        """
        클래스 Robot {
            move(dist) {
                나.position = 나.position + dist;
            }
        }
        """
    )


def test_상속과_부모_호출은_정상_통과한다():
    resolve(
        """
        클래스 Robot {
            move(dist) { 출력 "move"; }
        }
        클래스 SpeedRobot : Robot {
            move(dist) {
                부모.move(dist);
            }
        }
        """
    )


def test_클래스_외부에서_나를_사용하면_에러를_발생시킨다():
    with pytest.raises(ThisOutsideClassError):
        resolve("출력 나;")


def test_클래스_외부에서_부모를_사용하면_에러를_발생시킨다():
    with pytest.raises(SuperOutsideClassError):
        resolve("부모.move();")


def test_부모_없는_클래스에서_부모를_사용하면_에러를_발생시킨다():
    with pytest.raises(SuperWithoutSuperclassError):
        resolve(
            """
            클래스 Robot {
                move(dist) { 부모.move(dist); }
            }
            """
        )


def test_자기_자신을_상속하면_에러를_발생시킨다():
    with pytest.raises(SelfInheritanceError):
        resolve("클래스 Robot : Robot { }")


def test_생성자에서_값이_있는_반환을_사용하면_에러를_발생시킨다():
    with pytest.raises(ReturnInInitializerError):
        resolve(
            """
            클래스 Robot {
                생성자() { 반환 5; }
            }
            """
        )


def test_생성자에서_값이_없는_반환도_에러를_발생시킨다():
    with pytest.raises(ReturnInInitializerError):
        resolve(
            """
            클래스 Robot {
                생성자() { 반환; }
            }
            """
        )


def test_일반_메서드에서는_반환이_여전히_허용된다():
    resolve(
        """
        클래스 Robot {
            move(dist) { 반환 dist; }
        }
        """
    )


def test_생성자가_아닌_메서드_다음에_오는_생성자에서는_여전히_반환이_금지된다():
    with pytest.raises(ReturnInInitializerError):
        resolve(
            """
            클래스 Robot {
                move(dist) { 반환 dist; }
                생성자() { 반환 5; }
            }
            """
        )


def test_생성자_다음에_오는_일반_메서드에서는_반환_금지가_풀린다():
    # in_initializer 상태가 생성자 검사 후 다음 메서드로 새어나가지 않아야 한다
    resolve(
        """
        클래스 Robot {
            생성자() { }
            move(dist) { 반환 dist; }
        }
        """
    )
