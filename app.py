import streamlit as st
import pandas as pd
import numpy as np
from numpy.linalg import norm
from sklearn.feature_extraction.text import CountVectorizer
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
import tensorflow_hub as hub
from wordcloud import WordCloud, STOPWORDS
import tensorflow.compat.v1 as tf
import fasttext

tf.disable_v2_behavior()




#"""Pull in Keywords which similarity will be based upon"""
keywords = pd.read_csv("Indeed_ED_raw_data_dump.csv")
keyword_list = keywords["Short_Description"]
keyword_list = [i for i in keyword_list if str(i) !='nan']



all_text = " "
for i in keyword_list:
    all_text+=i
with open('train.txt', 'w', encoding="utf-8") as f:
    f.write(all_text)


elmo = hub.Module("https://tfhub.dev/google/elmo/2", trainable=True)
ft = fasttext.train_supervised("train.txt")

#fit vectorizer on the keywords
#"""

def elmo_vectors(x):
  embeddings=elmo(x, signature="default", as_dict=True)["elmo"]
  with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    sess.run(tf.tables_initializer())
    # return average of ELMo features
    return sess.run(tf.reduce_mean(embeddings,1))



# Create a Vectorizer Object
vectorizer = CountVectorizer()
vectorizer.fit(keyword_list)

def similarity_score_scikit(job_description_a, job_description_b):
  jda = vectorizer.transform([job_description_a])
  A = jda.toarray()[0]
  jdb = vectorizer.transform([job_description_b])
  B = jdb.toarray()[0]
  similarity = np.dot(A,B)/(norm(A)*norm(B))
  if np.isnan(similarity):
    return(0)
  else:
    return(similarity.round(4)*100)

def similarity_score_fasttext(job_description_a, job_description_b):
  A = ft.get_sentence_vector(job_description_a)
  B = ft.get_sentence_vector(job_description_b)
  print((cosine_similarity([A, B])))
  similarity = float(cosine_similarity([A, B])[0][1])
  if np.isnan(similarity):
    return(0)
  else:
    return round(similarity*100,4)

def similarity_score_elmo(job_description_a, job_description_b):
   A = elmo_vectors([job_description_a])[0]
   B = elmo_vectors([job_description_b])[0]
   similarity = float(cosine_similarity([A, B])[0][1])
   if np.isnan(similarity):
     return(0)
   else:
     return round(similarity*100,4)

def similarity_score(job_description_a, job_description_b, model):
  if model == 'Count vectorizer- scikit learn':
    return(similarity_score_scikit(job_description_a, job_description_b))
  elif model == 'ELMo':
    print("Warning !!! This will take some time - it requires patience")
    return(similarity_score_elmo(job_description_a, job_description_b))
  elif model == 'Fasttext':
    return(similarity_score_fasttext(job_description_a, job_description_b))


def plot_word_cloud(text_list):
  comment_words = ''
  stopwords = set(STOPWORDS)


  for val in text_list:
      
      # typecaste each val to string
      val = str(val)
  
      # split the value
      tokens = val.split()
      
      # Converts each token into lowercase
      for i in range(len(tokens)):
          tokens[i] = tokens[i].lower()
      
      comment_words += " ".join(tokens)+" "
  
  wordcloud = WordCloud(width = 800, height = 800,
                  background_color ='white',
                  stopwords = stopwords,
                  min_font_size = 10).generate(comment_words)
  return(wordcloud)

def main():
    
    # ===================== Set page config and background =======================
    # Main panel setup
    # Set website details
    st.set_page_config(page_title ="Job Description Similarity Scorer", 
                       page_icon=':desktop_computer:', 
                       layout='centered')
    """## Job description Similarity Scorer"""

    with st.expander("About"):
        st.write("This App checks for the similarity between two job descriptions and returns the score, the model uses certain keywords which can be found [here](https://docs.google.com/spreadsheets/d/1ILSICeRE3GQRiQGbRfoChAoP6PZSQt6f)")
   
    with st.expander("Settings"):
        model_option = st.selectbox('Kindly select preferred model',('Count vectorizer- scikit learn', 'ELMo','Fasttext'))
        # I used a slider to set-up an adjustable threshold
        demo = st.selectbox('Use Demo Texts',('No', 'Yes'))


    with st.form(key = 'form1', clear_on_submit=False):
        Job_description1 = st.text_area("First Job description")
        Job_description2 = st.text_area("Second Job description")
        Job_description3 = st.text_area("Third Job description")
        Job_description4 = st.text_area("Fourth Job description")
        Job_description5 = st.text_area("Fifth Job description")
        Job_description6 = st.text_area("Sixth Job description")
        submit_button = st.form_submit_button()

    if submit_button:
      job_description_list = [Job_description1,Job_description2,Job_description3,Job_description4,Job_description5,Job_description6]
      corr = pd.DataFrame(index = ["job description {}".format(i) for i in range(1,7)])
      for i in range(1,7):
        corr["job description {}".format(i)] = [similarity_score(job_description_list[i-1],job_description_list[k-1], model_option) for k in range(1,7)]
        most_correlated = corr["job description 1"][1:].idxmax()
      st.success("I'm processing your request")
      st.write("The most correlated Job description is {}".format(most_correlated))
      with st.expander("See More Analysis"):
        fig = plt.figure(figsize=(20, 12))
        sns.set(font_scale=2)
        sns.heatmap(corr, cmap="Greens")
        plt.title('Heatmap of similarities between all the job descriptions')
        st.pyplot(fig)
        st.write("The Similarity score between Job descriptions 1 and 2 is {}%".format(corr["job description 1".format(i)][1]))
        st.write("The Similarity score between Job descriptions 1 and 3 is {}%".format(corr["job description 1".format(i)][2]))
        st.write("The Similarity score between Job descriptions 1 and 4 is {}%".format(corr["job description 1".format(i)][3]))
        st.write("The Similarity score between Job descriptions 1 and 5 is {}%".format(corr["job description 1".format(i)][4]))
        st.write("The Similarity score between Job descriptions 1 and 6 is {}%".format(corr["job description 1".format(i)][5]))


        # plot the WordCloud image                      
        fig2 = plt.figure(figsize = (8, 8), facecolor = None)
        plt.imshow(plot_word_cloud(job_description_list))
        plt.axis("off")
        plt.title("Word cloud of the job descriptions")
        plt.tight_layout(pad = 0)
        st.pyplot(fig2)

if __name__ == "__main__":
    main()