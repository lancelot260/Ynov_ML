#!/usr/bin/env python3

# Libs unittest
import unittest
from unittest.mock import patch
from unittest.mock import Mock

# Utils libs
import os
import json
import numpy as np
import pandas as pd
from ynov import utils
from ynov.preprocessing import column_preprocessors

# Disable logging
import logging
logging.disable(logging.CRITICAL)


class ColumnPreprocessorsTests(unittest.TestCase):
    '''Main class to test all functions in ynov.preprocessing.column_preprocessors'''


    def setUp(self):
        '''SetUp fonction'''
        # On se place dans le bon répertoire
        # Change directory to script directory
        abspath = os.path.abspath(__file__)
        dname = os.path.dirname(abspath)
        os.chdir(dname)


    def test01_AutoLogTransform(self):
        '''Test de la classe column_preprocessors.AutoLogTransform'''
        # Vals à tester
        df = pd.DataFrame({
            'skewed_1': [1, 2, 3, 4, 5, 6, 7, 1000, 100000, 10000000] * 100,
            'not_skewed': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 100,
            'skewed_2': [-10000000, -100000, -1000, 1, 2, 3, 4, 5, 6, 7] * 100, # pour l'instant on accepte les négatifs, mais retourne des nans !
        })
        df_copy = df.copy(deep=True)
        arr = df.to_numpy()
        arr_copy = arr.copy()
        transformed_arr = pd.DataFrame({
            'skewed_1': np.log([1, 2, 3, 4, 5, 6, 7, 1000, 100000, 10000000] * 100),
            'not_skewed': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 100,
            'skewed_2': np.log([-10000000, -100000, -1000, 1, 2, 3, 4, 5, 6, 7] * 100),
        }).to_numpy()

        new_df =  pd.DataFrame({
            'toto': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'titi': [-10000000, -100000, -1000, 1, 2, 3, 4, 5, 6, 7],
            'tata': [5, 2, 4, 4, 5, 68, 7, 81, 9, -10],
        })
        new_df_copy = new_df.copy(deep=True)
        new_transformed_arr = pd.DataFrame({
            'toto': np.log([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            'titi': [-10000000, -100000, -1000, 1, 2, 3, 4, 5, 6, 7],
            'tata': np.log([5, 2, 4, 4, 5, 68, 7, 81, 9, -10]),
        }).to_numpy()

        # Fonctionnement nominal
        transformer = column_preprocessors.AutoLogTransform()
        transformer.fit(df)
        self.assertTrue(hasattr(transformer, 'fitted_'))
        self.assertEqual(transformer.applicable_columns_index, [0, 2])
        np.testing.assert_array_equal(transformer.transform(df), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(arr), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(new_df), new_transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)
        pd.testing.assert_frame_equal(new_df, new_df_copy)
        np.testing.assert_array_equal(arr, arr_copy)

        # Fonctionnement np array
        transformer = column_preprocessors.AutoLogTransform()
        transformer.fit(arr)
        self.assertEqual(transformer.applicable_columns_index, [0, 2])
        np.testing.assert_array_equal(transformer.transform(arr), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(arr), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(new_df), new_transformed_arr)
        np.testing.assert_array_equal(arr, arr_copy)
        pd.testing.assert_frame_equal(new_df, new_df_copy)
        np.testing.assert_array_equal(arr, arr_copy)

        # Fonctionnement nominal - fit_transform
        transformer = column_preprocessors.AutoLogTransform(min_skewness=1, min_amplitude=1000)
        self.assertEqual(transformer.applicable_columns_index, None)
        self.assertEqual(transformer.min_skewness, 1)
        self.assertEqual(transformer.min_amplitude, 1000)
        np.testing.assert_array_equal(transformer.fit_transform(df), transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)

        # Gestion erreurs
        transformer = column_preprocessors.AutoLogTransform()
        transformer.fit(df)
        with self.assertRaises(ValueError):
            transformer._validate_input(5)
        with self.assertRaises(ValueError):
            transformer._validate_input(np.array([[1, 0], [1, 1]]))


    def test02_ThresholdingTransform(self):
        '''Test de la classe column_preprocessors.ThresholdingTransform'''
        # Vals à tester
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'y': [1, 2, 3, 4, 5, 6, 7, 1000, 100000, 10000000, 100000000],
            'z': [1, 2, 3, 4, 5, 6, 156, 5648, 10000, 10001, 10002],
        })
        df_copy = df.copy(deep=True)
        arr = df.to_numpy()
        arr_copy = arr.copy()
        transformed_arr = pd.DataFrame({
            'x': [2, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6],
            'y': [1.5, 2, 3, 4, 5, 6, 7, 100, 100, 100, 100],
            'z': [1.5, 2, 3, 4, 5, 6, 156, 5648, 10000, 10001, 10001.5],
        }).to_numpy()

        new_df =  pd.DataFrame({
            'toto': [-10, -20, -5, 4, 5, 6, 7, 8, 9, 10, 11],
            'titi': [-10000000, -100000, -1000, 1, 2, 3, 4, 5, 6, 1000000, 100000000],
            'tata': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        })
        new_df_copy = new_df.copy(deep=True)
        new_transformed_arr = pd.DataFrame({
            'toto': [2, 2, 2, 4, 5, 6, 6, 6, 6, 6, 6],
            'titi': [1.5, 1.5, 1.5, 1.5, 2, 3, 4, 5, 6, 100, 100],
            'tata': [1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        }).to_numpy()

        # Fonctionnement nominal
        transformer = column_preprocessors.ThresholdingTransform(thresholds=[(2, 6), (None, 100), (None, None)])
        transformer.fit(df)
        self.assertTrue(hasattr(transformer, 'fitted_'))
        self.assertEqual(len(transformer.fitted_thresholds), 3)
        np.testing.assert_array_equal(transformer.transform(df), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(arr), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(new_df), new_transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)
        pd.testing.assert_frame_equal(new_df, new_df_copy)
        np.testing.assert_array_equal(arr, arr_copy)

        # Quantiles !=
        transformed_arr_quantiles_diff = pd.DataFrame({
            'x': [2, 2, 3, 4, 5, 6, 6, 6, 6, 6, 6],
            'y': [2, 2, 3, 4, 5, 6, 7, 100, 100, 100, 100],
            'z': [2, 2, 3, 4, 5, 6, 156, 5648, 10000, 10001, 10001],
        }).to_numpy()
        new_transformed_arr_quantiles_diff = pd.DataFrame({
            'toto': [2, 2, 2, 4, 5, 6, 6, 6, 6, 6, 6],
            'titi': [2, 2, 2, 2, 2, 3, 4, 5, 6, 100, 100],
            'tata': [2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        }).to_numpy()
        transformer = column_preprocessors.ThresholdingTransform(thresholds=[(2, 6), (None, 100), (None, None)], quantiles=(0.10, 0.90))
        transformer.fit(arr) # On fit sur une np array pour tester par la même occasion
        self.assertTrue(hasattr(transformer, 'fitted_'))
        self.assertEqual(len(transformer.fitted_thresholds), 3)
        np.testing.assert_array_equal(transformer.transform(df), transformed_arr_quantiles_diff)
        np.testing.assert_array_equal(transformer.transform(new_df), new_transformed_arr_quantiles_diff)
        pd.testing.assert_frame_equal(df, df_copy)
        pd.testing.assert_frame_equal(new_df, new_df_copy)

        # Fonctionnement nominal - fit_transform
        transformer = column_preprocessors.ThresholdingTransform(thresholds=[(2, 6), (None, 100), (None, None)])
        self.assertFalse(hasattr(transformer, 'fitted_'))
        self.assertEqual(len(transformer.fitted_thresholds), 0)
        np.testing.assert_array_equal(transformer.fit_transform(df), transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)

        # Gestion erreurs
        with self.assertRaises(ValueError):
            column_preprocessors.ThresholdingTransform(thresholds=None)
        with self.assertRaises(ValueError):
            column_preprocessors.ThresholdingTransform(thresholds=[(2, 6)], quantiles=5)
        with self.assertRaises(ValueError):
            column_preprocessors.ThresholdingTransform(thresholds=[(2, 6)], quantiles=(-1, 0.98))
        with self.assertRaises(ValueError):
            column_preprocessors.ThresholdingTransform(thresholds=[(2, 6)], quantiles=(5, 0.98))
        with self.assertRaises(ValueError):
            column_preprocessors.ThresholdingTransform(thresholds=[(2, 6)], quantiles=(0.05, -1))
        with self.assertRaises(ValueError):
            column_preprocessors.ThresholdingTransform(thresholds=[(2, 6)], quantiles=(0.05, 5))
        with self.assertRaises(ValueError):
            column_preprocessors.ThresholdingTransform(thresholds=[(2, 6)], quantiles=(0.95, 0.05))
        transformer = column_preprocessors.ThresholdingTransform(thresholds=[(2, 6), (None, 100), (None, None)])
        transformer.fit(df)
        with self.assertRaises(ValueError):
            transformer._validate_input(5)
        with self.assertRaises(ValueError):
            transformer._validate_input(np.array([[1, 0], [1, 1]]))


    def test03_AutoBinner(self):
        '''Test de la classe column_preprocessors.AutoBinner'''
        # Vals à tester
        # 4030 vals
        # threshold 0.05 -> 201.5
        # strategy = trehsold -> unique vals > 201 OK
        #
        df = pd.DataFrame({
            'x': ['a', 'b', 'b', 'c'] * 1000 + ['d', 'e', 'f'] * 10,
            'y': ['a', 'b', 'b', 'c'] * 1006 + ['d', 'e', 'f'] * 2,
            'z': ['a', 'b', 'b', 'c'] * 930 + ['d'] * 200 + ['e', 'f'] * 55,
        })
        df_copy = df.copy(deep=True)
        arr = df.to_numpy()
        arr_copy = arr.copy()
        transformed_arr = pd.DataFrame({
            'x': ['a', 'b', 'b', 'c'] * 1000 + ['other_', 'other_', 'other_'] * 10,
            'y': ['a', 'b', 'b', 'c'] * 1006 + ['other_', 'other_', 'other_'] * 2,
            'z': ['a', 'b', 'b', 'c'] * 930 + ['d'] * 200 + ['other_', 'other_'] * 55,
        }).to_numpy()

        new_df =  pd.DataFrame({
            'toto': ['a', 'g', 'b', 'c'] * 1000 + ['d', 'e', 'f'] * 10,
            'titi': ['d', 'd', 'e', 'f'] * 1006 + ['a', 'b', 'c'] * 2,
            'tata': ['i', 'j', 'b', 'c'] * 930 + ['d'] * 200 + ['e', 'f'] * 55,
        })
        new_df_copy = new_df.copy(deep=True)
        new_transformed_arr = pd.DataFrame({
            'toto': ['a', 'other_', 'b', 'c'] * 1000 + ['other_', 'other_', 'other_'] * 10,
            'titi': ['other_', 'other_', 'other_', 'other_'] * 1006 + ['a', 'b', 'c'] * 2,
            'tata': ['other_', 'other_', 'b', 'c'] * 930 + ['d'] * 200 + ['other_', 'other_'] * 55,
        }).to_numpy()

        # Fonctionnement nominal
        transformer = column_preprocessors.AutoBinner(strategy="auto", min_cat_count=3, threshold=0.05)
        transformer.fit(df)
        self.assertTrue(hasattr(transformer, 'fitted_'))
        self.assertEqual(transformer.n_features, 3)
        np.testing.assert_array_equal(transformer.transform(df), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(arr), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(new_df), new_transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)
        pd.testing.assert_frame_equal(new_df, new_df_copy)
        np.testing.assert_array_equal(arr, arr_copy)

        # Strategy threshold
        transformed_arr_strat_threshold = pd.DataFrame({
            'x': ['a', 'b', 'b', 'c'] * 1000 + ['other_', 'other_', 'other_'] * 10,
            'y': ['a', 'b', 'b', 'c'] * 1006 + ['other_', 'other_', 'other_'] * 2,
            'z': ['a', 'b', 'b', 'c'] * 930 + ['other_'] * 200 + ['other_', 'other_'] * 55,
        }).to_numpy()
        transformer = column_preprocessors.AutoBinner(strategy="threshold", min_cat_count=3, threshold=0.05)
        transformer.fit(arr) # On fit sur une np array pour tester par la même occasion
        np.testing.assert_array_equal(transformer.transform(df), transformed_arr_strat_threshold)

        # min_cat_count > nb categories
        new_transformed_arr_min_cat_count_sup = pd.DataFrame({
            'toto': ['a', 'other_', 'b', 'c'] * 1000 + ['d', 'e', 'f'] * 10,
            'titi': ['d', 'd', 'e', 'f'] * 1006 + ['a', 'b', 'c'] * 2,
            'tata': ['other_', 'other_', 'b', 'c'] * 930 + ['d'] * 200 + ['e', 'f'] * 55,
        }).to_numpy()
        transformer = column_preprocessors.AutoBinner(strategy="auto", min_cat_count=100, threshold=0.05)
        transformer.fit(df)
        np.testing.assert_array_equal(transformer.transform(df), arr)
        np.testing.assert_array_equal(transformer.transform(new_df), new_transformed_arr_min_cat_count_sup)

        # 1 seule cat inférieure threshold (on la garde)
        df_2_cats = pd.DataFrame({'x': ['a']* 100 + ['b'] *2})
        arr_2_cats = pd.DataFrame({'x': ['a']* 100 + ['b'] *2}).to_numpy()
        transformer = column_preprocessors.AutoBinner(strategy="auto", min_cat_count=0, threshold=0.05)
        transformer.fit(df_2_cats)
        self.assertEqual(transformer.n_features, 1)
        np.testing.assert_array_equal(transformer.transform(df_2_cats), arr_2_cats)

        # Fonctionnement nominal - fit_transform
        transformer = column_preprocessors.AutoBinner(strategy="auto", min_cat_count=3, threshold=0.05)
        self.assertFalse(hasattr(transformer, 'fitted_'))
        self.assertEqual(transformer.n_features, None)
        np.testing.assert_array_equal(transformer.fit_transform(df), transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)

        # Gestion erreurs
        with self.assertRaises(ValueError):
            column_preprocessors.AutoBinner(strategy='toto')
        with self.assertRaises(ValueError):
            column_preprocessors.AutoBinner(min_cat_count='toto')
        with self.assertRaises(ValueError):
            column_preprocessors.AutoBinner(min_cat_count=-1)
        with self.assertRaises(ValueError):
            column_preprocessors.AutoBinner(threshold='toto')
        with self.assertRaises(ValueError):
            column_preprocessors.AutoBinner(threshold=-1)
        transformer = column_preprocessors.AutoBinner(strategy="threshold", min_cat_count=3, threshold=0.05)
        transformer.fit(df)
        with self.assertRaises(ValueError):
            transformer._validate_input(5)
        with self.assertRaises(ValueError):
            transformer._validate_input(np.array([[1, 0], [1, 1]]))


    def test04_EmbeddingTransformer(self):
        '''Test de la classe column_preprocessors.EmbeddingTransformer'''
        # Vals à tester
        embedding = {'toto': [1., 5., 8.], 'titi': [-1., 3., 4.], 'tata': [-8., -6., 2.64]}
        df = pd.DataFrame({
            'x': ['toto', 'tata', 'titi'],
            'y': ['titi', 'test', 'toto'],
        })
        df_copy = df.copy(deep=True)
        arr = df.to_numpy()
        arr_copy = arr.copy()
        transformed_arr = pd.DataFrame({
            'x1': [1., -8., -1.],
            'x2': [5., -6., 3.],
            'x3': [8., 2.64, 4.],
            'y1': [-1., 0., 1.],
            'y2': [3., 0., 5.],
            'y3': [4., 0., 8.],
        }).to_numpy()

        new_df =  pd.DataFrame({
            'x': ['test', 'tata', 'tata'],
            'y': ['titi', 'tata', 'toto'],
        })
        new_df_copy = new_df.copy(deep=True)
        new_transformed_arr = pd.DataFrame({
            'x1': [0., -8., -8.],
            'x2': [0., -6., -6.],
            'x3': [0., 2.64, 2.64],
            'y1': [-1., -8., 1.],
            'y2': [3., -6., 5.],
            'y3': [4., 2.64, 8.],
        }).to_numpy()


        # Fonctionnement nominal
        transformer = column_preprocessors.EmbeddingTransformer(embedding=embedding)
        transformer.fit(df)
        self.assertTrue(hasattr(transformer, 'fitted_'))
        self.assertEqual(transformer.n_features, 2)
        self.assertEqual(transformer.embedding_size, 3)
        np.testing.assert_array_equal(transformer.transform(df), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(arr), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(new_df), new_transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)
        pd.testing.assert_frame_equal(new_df, new_df_copy)
        np.testing.assert_array_equal(arr, arr_copy)

        # Fonctionnement nominal - fit_transform
        transformer = column_preprocessors.EmbeddingTransformer(embedding=embedding)
        self.assertEqual(transformer.n_features, None)
        self.assertEqual(transformer.embedding_size, 3)
        np.testing.assert_array_equal(transformer.fit_transform(df), transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)

        # JSON file
        json_path = os.path.join(os.getcwd(), 'tmp_json_tests.json')
        if os.path.exists(json_path):
            os.remove(json_path)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(embedding, f, indent=4)
        transformer = column_preprocessors.EmbeddingTransformer(embedding=json_path)
        transformer.fit(df)
        self.assertTrue(hasattr(transformer, 'fitted_'))
        self.assertEqual(transformer.n_features, 2)
        self.assertEqual(transformer.embedding_size, 3)
        np.testing.assert_array_equal(transformer.transform(df), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(arr), transformed_arr)
        np.testing.assert_array_equal(transformer.transform(new_df), new_transformed_arr)
        pd.testing.assert_frame_equal(df, df_copy)
        pd.testing.assert_frame_equal(new_df, new_df_copy)
        np.testing.assert_array_equal(arr, arr_copy)
        os.remove(json_path)

        # get_feature_names
        transformer = column_preprocessors.EmbeddingTransformer(embedding=embedding)
        transformer.fit(arr) # On fit sur une np array pour tester par la même occasion
        features_out = transformer.get_feature_names(['toto', 'test'])
        expected_features_out = np.array([
            'emb_toto_0', 'emb_toto_1', 'emb_toto_2',
            'emb_test_0', 'emb_test_1', 'emb_test_2',
        ])
        np.testing.assert_array_equal(features_out, expected_features_out)

        # Gestion erreurs
        with self.assertRaises(TypeError):
            column_preprocessors.EmbeddingTransformer(embedding=5)
        with self.assertRaises(ValueError):
            column_preprocessors.EmbeddingTransformer(embedding=embedding, none_strategy='toto')
        with self.assertRaises(ValueError):
            column_preprocessors.EmbeddingTransformer(embedding='toto.csv')
        with self.assertRaises(FileNotFoundError):
            column_preprocessors.EmbeddingTransformer(embedding='not_a_correct_path.json')
        transformer = column_preprocessors.EmbeddingTransformer(embedding=embedding)
        transformer.fit(df)
        with self.assertRaises(ValueError):
            transformer._validate_input(5)
        with self.assertRaises(ValueError):
            transformer._validate_input(np.array([[1, 0, 4], [1, 1, 5]]))


# Execution des tests
if __name__ == '__main__':
    # Start tests
    unittest.main()