#!/bin/bash
kubectl delete configmap train-word2vec
kubectl create configmap train-word2vec --from-file=Word2Vec.py --from-file=hebrew_stopwords.txt
kubectl delete -f ./word2vec_trainer.yaml
kubectl apply -f ./word2vec_trainer.yaml
