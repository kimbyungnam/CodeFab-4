import pytest

from codefab.assembler.assembler import Assembler
from codefab.checker import Checker
from codefab.error import (
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
