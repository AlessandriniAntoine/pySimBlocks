import numpy as np
import pytest

from pySimBlocks.blocks.sources.constant import Constant


# ------------------------------------------------------------
# 1) Test valeur simple (scalaire)
# ------------------------------------------------------------
def test_constant_scalar():
    c = Constant("c", 5.0)
    c.initialize(0.0)
    assert np.allclose(c.outputs["out"], [[5.0]])


# ------------------------------------------------------------
# 2) Test vecteur colonne (n,1)
# ------------------------------------------------------------
def test_constant_vector():
    c = Constant("c", [[1.0], [2.0], [3.0]])
    c.initialize(0.0)
    assert np.allclose(c.outputs["out"], [[1.0], [2.0], [3.0]])


# ------------------------------------------------------------
# 3) Test reshape depuis vecteur ligne ou liste 1D
# ------------------------------------------------------------
def test_constant_1d_list():
    c = Constant("c", [10.0, 20.0])
    c.initialize(0.0)
    assert np.allclose(c.outputs["out"], [[10.0], [20.0]])

# ------------------------------------------------------------
# 4) Test matrice (m,n)
# ------------------------------------------------------------
def test_constant_matrix():
    c = Constant("c", [[1.0, 2.0], [3.0, 4.0]])
    c.initialize(0.0)
    assert np.allclose(c.outputs["out"], [[1.0, 2.0], [3.0, 4.0]])


# ------------------------------------------------------------
# 5) Test erreur : valeur non numérique
# ------------------------------------------------------------
def test_constant_invalid_type():
    with pytest.raises(TypeError):
        Constant("c", value="not numeric")


# ------------------------------------------------------------
# 6) Test erreur : mauvaise forme (simulateur ne joue pas de rôle ici)
# ------------------------------------------------------------
def test_constant_bad_shape():
    with pytest.raises(ValueError):
        Constant("c", value=np.zeros((2, 3, 2)))
