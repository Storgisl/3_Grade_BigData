import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split 

global HEADER, df

HEADER = list(pd.read_csv("data/Голосование_конгресса.txt", sep="\t", nrows=1, encoding="Windows-1251").columns)
df = pd.read_csv("data/голосование_конгресса.txt", skiprows=1, header=None, names=HEADER, encoding="Windows-1251", sep="\t")

class Checker:
    def unique_vals(self, rows, col):
        """Find the unique values for a column in a dataset."""
        return set([row[col] for row in rows])

    def class_counts(self, rows):
        counts = {}
        for row in rows:
            label = row[0]
            if label not in counts:
                counts[label] = 0
            counts[label] += 1
        return counts
    
    def is_numeric(self, value):
        """Test if a value is numeric."""
        return isinstance(value, int) or isinstance(value, float)

class Question:
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def match(self, example):
        # Compare the feature value in an example to the
        # feature value in this question.
        val = example[self.column]
        checker = Checker()
        if checker.is_numeric(val):
            return val >= self.value
        else:
            return val == self.value

    def __repr__(self):
        # This is just a helper method to print
        # the question in a readable format.
        condition = "=="
        checker = Checker()
        if checker.is_numeric(self.value):
            condition = ">="
        return "Is %s %s %s?" % (
            HEADER[self.column], condition, str(self.value))

class Node:
    def __init__(self, left, right, value, threshold):
        self.left = left
        self.right = right
        self.value = value
        self.threshold = threshold

class Leaf:
    """A Leaf node classifies data.

    This holds a dictionary of class (e.g., "Apple") -> number of times
    it appears in the rows from the training data that reach this leaf.
    """

    def __init__(self, rows):
        checker = Checker()
        self.predictions = checker.class_counts(rows)

class Decision_Node:
    """A Decision Node asks a question.

    This holds a reference to the question, and to the two child nodes.
    """

    def __init__(self,
                 question,
                 true_branch,
                 false_branch):
        
        self.question = question
        self.true_branch = true_branch
        self.false_branch = false_branch

class DecisionTreeClassifier:
    def partition(self, rows, question):
        """Partitions a dataset.

        For each row in the dataset, check if it matches the question. If
        so, add it to 'true rows', otherwise, add it to 'false rows'.
        """
        true_rows, false_rows = [], []
        for row in rows:
            if question.match(row):
                true_rows.append(row)
            else:
                false_rows.append(row)
        return true_rows, false_rows
    
    def gini(self, rows):
        """Calculate the Gini Impurity for a list of rows.

        There are a few different ways to do this, I thought this one was
        the most concise. See:
        https://en.wikipedia.org/wiki/Decision_tree_learning#Gini_impurity
        """
        checker = Checker()
        counts = checker.class_counts(rows)
        impurity = 1
        for lbl in counts:
            prob_of_lbl = counts[lbl] / float(len(rows))
            impurity -= prob_of_lbl**2
        return impurity
    
    def info_gain(self, left, right, current_uncertainty):
        """Information Gain.

        The uncertainty of the starting node, minus the weighted impurity of
        two child nodes.
        """
        p = float(len(left)) / (len(left) + len(right))
        return current_uncertainty - p * self.gini(left) - (1 - p) * self.gini(right)
    
    def find_best_split(self, rows):
        """Find the best question to ask by iterating over every feature / value
        and calculating the information gain."""
        best_gain = 0  # keep track of the best information gain
        best_question = None  # keep train of the feature / value that produced it
        current_uncertainty = self.gini(rows)
        n_features = len(rows[0]) - 1  # number of columns # number of columns

        for col in range(n_features):  # for each feature

            values = set([row[col] for row in rows])  # unique values in the column

            for val in values:  # for each value

                question = Question(col, val)

                # try splitting the dataset
                true_rows, false_rows = self.partition(rows, question)

                # Skip this split if it doesn't divide the
                # dataset.
                if len(true_rows) == 0 or len(false_rows) == 0:
                    continue

                # Calculate the information gain from this split
                gain = self.info_gain(true_rows, false_rows, current_uncertainty)

                # You actually can use '>' instead of '>=' here
                # but I wanted the tree to look a certain way for our
                # toy dataset.
                if gain >= best_gain:
                    best_gain, best_question = gain, question

        return best_gain, best_question
    
    def build_tree(self, rows):
        """Builds the tree.

        Rules of recursion: 1) Believe that it works. 2) Start by checking
        for the base case (no further information gain). 3) Prepare for
        giant stack traces.
        """

        # Try partitioing the dataset on each of the unique attribute,
        # calculate the information gain,
        # and return the question that produces the highest gain.
        gain, question = self.find_best_split(rows)

        # Base case: no further info gain
        # Since we can ask no further questions,
        # we'll return a leaf.
        if gain == 0:
            return Leaf(rows)

        # If we reach here, we have found a useful feature / value
        # to partition on.  
        true_rows, false_rows = self.partition(rows, question)

        # Recursively build the true branch.
        true_branch = self.build_tree(true_rows)

        # Recursively build the false branch.
        false_branch = self.build_tree(false_rows)

        # Return a Question node.
        # This records the best feature / value to ask at this point,
        # as well as the branches to follow
        # dependingo on the answer.
        return Decision_Node(question, true_branch, false_branch)
    
    def print_tree(self, node, spacing=""):
        """World's most elegant tree printing function."""

        # Base case: we've reached a leaf
        if isinstance(node, Leaf):
            print (spacing + "Predict", node.predictions)
            return

        # Print the question at this node
        print (spacing + str(node.question))

        # Call this function recursively on the true branch
        print (spacing + '--> True:')
        self.print_tree(node.true_branch, spacing + "  ")

        # Call this function recursively on the false branch
        print (spacing + '--> False:')
        self.print_tree(node.false_branch, spacing + "  ")

    def classify(self, row, node):
        """See the 'rules of recursion' above."""

        # Base case: we've reached a leaf
        if isinstance(node, Leaf):
            return node.predictions

        # Decide whether to follow the true-branch or the false-branch.
        # Compare the feature / value stored in the node,
        # to the example we're considering.
        if node.question.match(row):
            return self.classify(row, node.true_branch)
        else:
            return self.classify(row, node.false_branch)    
        
    def print_leaf(self, counts):
        """A nicer way to print the predictions at a leaf."""
        total = sum(counts.values()) * 1.0
        probs = {}
        for lbl in counts.keys():
            probs[lbl] = str(int(counts[lbl] / total * 100)) + "%"
        return probs
    
def main():
    tree = DecisionTreeClassifier()

    train_proportion = 0.8
    train_size = int(len(df) * train_proportion)
    
    train_data = df.iloc[:train_size, :].to_numpy()
    test_data = df.iloc[train_size:, :].to_numpy()
    
    tree_1 = tree.build_tree(train_data)

    for row in test_data:
        print ("Actual: %s. Predicted: %s" %
               (row[0], tree.print_leaf(tree.classify(row, tree_1))))
        
if __name__=="__main__":
    main()