import lightgbm as lgb
import pandas as pd
from sklearn import svm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler

company_model_parameters = dict(rf=dict(cr=dict(n_estimators=500, min_samples_leaf=5, max_features=1, oob_score=True),
                                        cr_ti=dict(n_estimators=120, max_features=0.5, max_depth=20, oob_score=True, bootstrap=True,
                                                   criterion='squared_error'),
                                        ti=dict(n_estimators=150, max_depth=12, max_features=1, oob_score=True)),
                                svr=dict(cr=dict(max_iter=1e6, C=10, tol=1e-5, epsilon=1e-5, gamma=9e-3
                                                 # max_iter=1e6, C=0.005, tol=1e-3, epsilon=0.002
                                                 ),
                                         ti=dict(max_iter=1e6, C=0.5, tol=1e-4, gamma='scale', epsilon=1e-3),
                                         # ti=dict(max_iter=1e6, C=0.2, tol=1e-3, gamma='scale', epsilon=1e-4)))
                                         cr_ti=dict(max_iter=1e6, C=50, tol=5e-3, epsilon=1e-4, gamma=3e-3)
                                         ),
                                lgb=dict(ti=dict(
                                    # n_estimators=1000, n_jobs=-1, max_depth=10
                                    # , learning_rate=5e-3
                                    # , colsample_bytree=.2
                                    # , subsample=0.3
                                    # # ,boosting_type='goss'
                                    # n_estimators=500, n_jobs=-1
                                    # , learning_rate=5e-2
                                    # , colsample_bytree=.3
                                    # , subsample=0.8
                                    # , bagging_fraction=0.3
                                    # , bagging_freq=21
                                    # , num_leaves=21
                                    # n_estimators=1000
                                    # # ,max_depth=12
                                    # , learning_rate=5e-2
                                    # , colsample_bytree=.5
                                    # , subsample=0.1
                                    # , bagging_fraction=0.2
                                    # , bagging_freq=5
                                    # , num_leaves=21
                                    num_leaves=21,
                                    n_estimators=100,
                                    learning_rate=5e-2,
                                    max_depth=8,
                                    colsample_bytree=.2,
                                    subsample=.8,
                                    reg_alpha=1e-3,
                                ),
                                    cr=dict(
                                        # n_estimators=500, learning_rate=5e-2
                                        # , bagging_fraction=0.1, bagging_freq=5,

                                        bagging_fraction=.65, num_leaves=252, n_estimators=220, learning_rate=4e-2,
                                        max_depth=7, reg_alpha=9e-4
                                    ),
                                    cr_ti=dict(n_estimators=250, learning_rate=0.09, reg_lambda=1e-2, max_depth=7, reg_alpha=1e-3,
                                               feature_fraction=0.3, subsample=.3, objective='fair', bagging_seed=42, )
                                )
                                )

sector_model_parameters = dict(rf=dict(cr=dict(n_estimators=300, bootstrap=True, max_samples=0.5, max_features='sqrt'),
                                       ti=dict(n_estimators=100, max_depth=40, bootstrap=True, max_samples=0.7, max_features='sqrt'),
                                       cr_ti=dict(n_estimators=150, bootstrap=True, max_samples=0.7, max_features=1, max_depth=60)
                                       ),
                               svr=dict(
                                   # cr=dict(max_iter=1e6, C=0.005, tol=1e-3, epsilon=0.002, gamma='scale'),
                                   cr=dict(max_iter=1e6, C=2, tol=1e-4, epsilon=1e-4, gamma='scale'),
                                   ti=dict(max_iter=1e6, C=2, tol=1e-5, epsilon=0.025, gamma='scale'),
                                   # ti=dict(max_iter=1e6, C=0.2, tol=1e-3, gamma='scale', epsilon=1e-4)))
                                   cr_ti=dict(max_iter=1e6, C=2, tol=1e-4, epsilon=0.05, gamma='scale')
                               ),
                               lgb=dict(ti=dict(
                                   # num_leaves=230, n_estimators=150, learning_rate=6e-2, max_depth=20,
                                   # colsample_bytree=.7, subsample=.2, objective='fair'
                                   # n_estimators=200, num_leaves=63, colsample_bytree=1,
                                   # learning_rate=0.05, subsample=0.3, max_depth=8,
                                   # objective='fair'
                                   # num_leaves=230, n_estimators=150, learning_rate=6e-2, max_depth=20,
                                   # colsample_bytree=.7, subsample=.2, objective='fair'
                                   # n_estimators=200, num_leaves=63, colsample_bytree=1,
                                   # learning_rate=0.05, subsample=0.3, max_depth=8,
                                   # objective='fair'
                                   # n_estimators=150, num_leaves=63, colsample_bytree=0.4,
                                   # learning_rate=0.05, subsample=0.3,
                                   # objective='fair'
                                   n_estimators=100, num_leaves=100, colsample_bytree=0.8, max_depth=15,
                                   learning_rate=0.03, subsample=0.8,

                               ),
                                   cr=dict(
                                       num_leaves=230, n_estimators=250, learning_rate=67e-3,
                                       max_depth=12, colsample_bytree=.9, objective='fair'
                                   ),
                                   cr_ti=dict(num_leaves=100, n_estimators=150, learning_rate=0.09, feature_fraction=0.75, subsample=.5,
                                              objective='fair', bagging_seed=42, )
                               )
                               )


def get_model(model_type, data_type, prediction_type):
    if prediction_type == 'company':
        model_parameters = company_model_parameters
    else:
        model_parameters = sector_model_parameters
    model_dict = dict(rf=Pipeline([
        ('scale', MinMaxScaler(feature_range=(-1, 1))),
        ('regressor', RandomForestRegressor(**model_parameters['rf'][data_type], random_state=42, n_jobs=-1))
    ]),
        svr=Pipeline([
            ('scale', MinMaxScaler(feature_range=(-1, 1))),
            ('regressor', svm.SVR(**model_parameters['svr'][data_type]))
        ]),
        lgb=Pipeline([
            ('scale', MinMaxScaler(feature_range=(-1, 1))),
            ('regressor',
             lgb.LGBMRegressor(**model_parameters['lgb'][data_type], random_state=42, n_jobs=-1))
        ])
    )
    if model_type not in model_dict.keys():
        raise ValueError("Model not found in list")
    return model_dict[model_type]


def get_fit_regressor(x_train, y_cr_train, x_validation, y_validation, x_test, y_cr_test, data_type='cr',
                      model_type='rf', prediction_type='company', context=None,
                      columns=None,
                      get_cross_validation_results=False, suffix=None):
    if columns is not None:
        X_train, y_train = x_train[columns].copy(), y_cr_train.copy()
        X_validation, y_validation = x_validation[columns].copy(), y_validation.copy()
        X_test, y_test = x_test[columns].copy(), y_cr_test.copy()
    else:
        X_train, y_train = x_train.copy(), y_cr_train.copy()
        X_validation, y_validation = x_validation.copy(), y_validation.copy()
        X_test, y_test = x_test.copy(), y_cr_test.copy()

    print('train', X_train.shape, y_train.shape)
    print('validation', X_validation.shape, y_validation.shape)
    print('test', X_test.shape, y_test.shape)

    regressor = get_model(model_type=model_type, data_type=data_type, prediction_type=prediction_type)
    score = None
    if get_cross_validation_results:
        if x_validation is None or len(x_validation) == 0:
            raise ValueError("Should provide a validation set")
        x, y = pd.concat([X_train, X_validation]), pd.concat([y_train, y_validation])

        cv = TimeSeriesSplit(max_train_size=int(2 * len(x) / 3), n_splits=10)
        score = cross_validate(regressor, x.values, y.values.ravel(),
                               scoring=['r2', 'neg_mean_absolute_error', 'neg_mean_squared_error'], n_jobs=-1,
                               verbose=0, cv=cv)

    regressor.fit(X_train.values, y_train.values.ravel())
    y_hat = regressor.predict(X_test.values)
    y_test['predicted'] = y_hat.reshape(-1, 1)

    y_hat_val = regressor.predict(X_validation.values)
    y_validation['predicted'] = y_hat_val.reshape(-1, 1)
    if suffix:
        y_test = y_test.add_suffix(suffix)
        y_validation = y_validation.add_suffix(suffix)

    print('validation', X_validation.shape, y_validation.shape)
    print('test', X_test.shape, y_test.shape)
    return regressor, y_validation, y_test, score
