import numpy as np
from sklearn.model_selection import train_test_split
import random


def extract_tags(tag_scores, movie_tag_rel, last_movie_id, top):
    tags = sorted(tag_scores, key=lambda x: x[1])[-top:]
    movie_tag_rel[last_movie_id] = [x[0] for x in tags]
    tag_scores.clear()


def extract_movie_tag_relation(filepath, top=10):
    movie_tag_rel = {}
    with open(filepath, "r") as f:
        f.readline()
        last_movie_id, tag_scores = None, []
        for line in f.readlines():
            line = line.strip()
            splitted = line.split(",")
            movie_id, tag_id, score = splitted[0], splitted[1], float(splitted[2])
            if last_movie_id is not None and movie_id != last_movie_id:
                extract_tags(tag_scores, movie_tag_rel, last_movie_id, top)
            tag_scores.append((tag_id, score))
            last_movie_id = movie_id
        
        extract_tags(tag_scores, movie_tag_rel, last_movie_id, top)

    return movie_tag_rel


def extract_movie_cate_relation(filepath):
    cate_encoder, cate_decoder, cate_id = {}, [], 0
    movie_cate_rel = {}
    with open(filepath, "r", encoding="utf-8") as f:
        f.readline()
        for line in f.readlines():
            cates_encoded = []
            line = line.strip()
            splitted = line.split(",")
            cates, movie_id = splitted[-1].split("|"), splitted[0]
            for cate in cates:
                if cate in cate_encoder:
                    cates_encoded.append(cate_encoder[cate])
                else:
                    cates_encoded.append(cate_id)
                    cate_encoder[cate] = cate_id
                    cate_decoder.append(cate)
                    cate_id += 1
            movie_cate_rel[movie_id] = cates_encoded
    
    return movie_cate_rel, cate_encoder, cate_decoder
            

def extract_user_behaviors(filepath):
    user_behaviors = {}
    pos, neg = 0, 0
    with open(filepath, "r") as f:
        f.readline()
        for line in f.readlines():
            line = line.strip()
            splitted = line.split(",")
            user_id, movie_id, rating, timestamp = splitted[0], splitted[1], float(splitted[2]), int(splitted[3])
            if user_id not in user_behaviors:
                user_behaviors[user_id] = []
            if rating <= 1.5:
                user_behaviors[user_id].append((movie_id, 0, timestamp))
                neg += 1
            elif rating >= 3.5:
                user_behaviors[user_id].append((movie_id, 1, timestamp))
                pos += 1
    print("pos: {}, neg: {}".format(pos, neg)) 

    for user_id, behavior in user_behaviors.items():
        # sort behavior by time, use top 80% to build history feature 
        # and last 20% as label
        behavior_sorted = sorted(behavior, key=lambda x: x[2])
        pivot = int(len(behavior) * 0.8)
        X, Y = behavior[:pivot], behavior[pivot:]
        user_behaviors[user_id] = {"X": X, "Y": Y}

    return user_behaviors


def split_users(users):
    train, test = [], []
    for user in users:
        seed = random.randint(1, 10)
        if seed <= 2:
            test.append(user)
        else:
            train.append(user)

    return train, test


def generate_user_samples(user_id, histories, futures, movie_tag_map, movie_cate_map, samples):
    # build features
    # list features no deduplicating
    pos_tags, neg_tags, pos_cates, neg_cates = [], [], [], []
    for movie_id, action, timestamp in histories:
        try:
            movie_tags, movie_cates = movie_tag_map[movie_id], movie_cate_map[movie_id]
        except KeyError:
            continue
        if action == 1:
            pos_tags += movie_tags
            pos_cates += movie_cates
        else:
            neg_tags += movie_tags
            neg_cates += movie_cates
    # each user has one X
    X = (user_id, pos_tags, neg_tags, pos_cates, neg_cates)

    # build labels, each user has multi Ys
    for movie_id, action, timestamp in futures:
        try:
            movie_tags = movie_tag_map[movie_id]
        except KeyError:
            continue
        samples.append([X, (movie_tags, action)])


def generate_samples(train_users, test_users, user_behaviors, movie_tag_map, movie_cate_map):
    train_samples, test_samples = [], []
    for user_id in train_users:
        histories, futures = user_behaviors[user_id]["X"], user_behaviors[user_id]['Y']
        generate_user_samples(user_id, 
                              histories, 
                              futures, 
                              movie_tag_map, 
                              movie_cate_map, 
                              train_samples)

    for user_id in test_users:
        histories, futures = user_behaviors[user_id]["X"], user_behaviors[user_id]['Y']
        generate_user_samples(user_id, 
                              histories, 
                              futures, 
                              movie_tag_map, 
                              movie_cate_map, 
                              test_samples)
    
    return train_samples, test_samples
 