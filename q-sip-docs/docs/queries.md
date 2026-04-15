## Queries

A lot of this section is paraphrased from Romain Moyard's [article](https://pennylane.ai/qml/demos/tutorial_zx_calculus), published on Pennylane in 2023.
The images in this section are also from Romain Moyard's article.

| Query  | Status |   Description   |
|--------|--------|-----------------|
| query1 |  ✅ | Proven valid |
| query2 | ⚠️   |  Sometimes fails   |
| query3 | ❌ | Does not work |

**ZX calculus rules:**

As the X-gate and Z-gate are not commutative, vertices without a phase that have a different color, do not commute.
Commutatitivity is a property of an operation, where changing the order of the operands does not affect the result, like $5 + 2 = 2 + 5$, but $\frac{2}{5} \neq \frac{5}{2}$.

-----

1. Fuse rule

    ![the fuse rule](images/f_rule.jpeg)

    The fuse rule can be applied when two spiders of the same type are connected by one or more wires. 
    The resulting fused part of the graph is a spider with the phase as the sum of the phases of the two spiders.

    This rule is implemented by:

    xxxx

    ---

2. π-copy rule

    ![the π-copy rule](images/pi_rule.jpeg)

    The π-copy rule allows one to "pull through" an X-gate through a Z-spider (or Z-gate through an X-spider).
    Due to X and Z being anticommutative, the phase of the Z-gate becomes negative.

    This rule is implemented by:

    xxxx

    ---

3. State-copy rule

    ![the state copy rule](images/c_rule.jpg)

    The state-copy rule tells us how simple, one-qubit states interact with a spider of the opposite colour.
    As it is only valid for states that are multiples of π.
    In this diagram, $a \in \mathbb{Z}$.
    This can be summarised as if you pull a basis state through an opposite colour spider, the basis state will be copied to each outgoing wire.

    This rule is implemented by:

    xxxx

    ---

4. Identity rule

    ![the identity rule](images/id_rule.jpeg)

    According to the identity rule, if there is a spider that is: 

    A) phaseless and 

    B) has one input and one output, 

    it is equivalent to an identity and can be removed.
    Thanks to this rule, we can get rid of self-loops.

    This rule is implemented by:

    xxxx

    ---

5. Bialgebra Rule

    ![the bialgebra rule](images/b_rule.jpg)

    A bialgebra is a structure where we have one product (combines two wires to one) and one coproduct (split a wire to two wires).
    For a bialgebra, we can pull a product through a coproduct, at the cost of doubling.

    This rule is implemented by:

    xxxx

    ---

6. Hopf rule

    ![Hopf rule](images/hopf_rule.jpeg)

    The Hopf rule reminds of the bialgebra rule: it is in some sense the opposite of the bialgebra rule.
    In it we pull a coproduct through a product, but instead of doubling, this time, the wires decouple.
    This rule follows from the bialgebra and state-copy rules, but it is often documented as its own rule.

    This rule is implemented by:

    xxxx

    ---



**Auxiliary queries:**

There are some queries outside the ZX calculus rules.
Most often these exist for computational reasons, like combining two queries that are very often used after another in a sequence.
