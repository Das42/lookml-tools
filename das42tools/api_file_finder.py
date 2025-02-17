import looker_sdk
from looker_sdk import models40
import json
import pandas as pd
import sys

sdk = looker_sdk.init40(config_file = '../looker_api/looker.ini', section = 'Looker')

def dict_to_df(d):
    df = pd.DataFrame(columns = ['model', 'explore', 'view'])
    for model in d.keys():
        for explore in d[model].keys():
            for view in d[model][explore]:
                df.loc[len(df.index)] = [model, explore, view]
    return df
    
def list_files_in_project(lookml_project):

    views = list(filter(lambda x: x['type'] == 'view', sdk.all_project_files(project_id = lookml_project)))
    view_names = list(view['id'].split('.view.lkml')[0] for view in views)
    view_names = list(map(lambda x: x.lower().split('/')[-1], view_names))
    models = filter(lambda x: x['type'] == 'model', sdk.all_project_files(project_id = lookml_project))
    model_names = (model['id'].split('.model.lkml')[0] for model in models)
    
    print('views and models parsed')

    project_dict = dict({})

    for model_name in model_names:
        explores = sdk.lookml_model(model_name)['explores']
        explore_dict = dict({})

        for explore in explores:
            ex = sdk.lookml_model_explore(model_name, explore['name'])
            views = []
            views.append(ex['view_name'])
            for join in ex['joins']:
                views.append(join['name'])
            explore_dict[explore['name']] = views
        
        project_dict[model_name] = explore_dict
    
    print('dictionary built')
    
    project_df = dict_to_df(project_dict)

    project_df['view_file_missing'] = project_df['view'].apply(lambda x: x not in view_names)
    
    print('missing views identified')

    project_df['is_orphan'] = False

    for view in view_names:
        if view not in project_df['view'].values:
            project_df.loc[len(project_df.index)] = ['', '', view, False, True]
        
    missing_views = project_df[project_df['view_file_missing'] == True]['view']

    for view in missing_views:
        with open(f'../lookml-square-risk/{view}.view.lkml', 'w') as file:
            file.write(f'view: {view} {{}}\n\n#Added to enable grapher to run')
    
    print('missing view files created')
    
    print('orphan views identified')
            
    project_df.to_csv(f'{lookml_project}_files.csv')
    
    print('csv created')
    
if __name__ == "__main__":
    list_files_in_project(sys.argv[1])