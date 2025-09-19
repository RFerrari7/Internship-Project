




```
.
├── MA data                        # data used for the analysis
│   ├── tbl_addresses.csv           # contains info on address corresponding to a customer account
│   ├── tbl_customer_accounts.csv   # contains info on the loyalty account associated to the customers
│   ├── tbl_customer_reviews.csv    # contains the reviews made by the customers
│   ├── tbl_customers.csv           # contains info on the customers
│   ├── tbl_labelled_reviews.csv    # contains a set of review texts with the sentiment labels assigned (ground-truth)
│   ├── tbl_orders.csv              # contains all the orders made by the customers, i.e. all the products purchased or refunded
│   └── tbl_products.csv            # contains info on the products
├── MA notebooks                   # notebooks containing the source code
│   ├── 1.Preprocessing.ipynb       # preprocessing operations
│   ├── 2.EDA.ipynb                 # exploratory data analysis
│   ├── 3.RFM+Churn+MBA.ipynb       # implementation of the methods descrpited before
│   ├── 4.Sentiment analysis.ipynb  # sentiment analysis conducted with BERT
│   └── 5.Extra Point 1+2.ipynb     # sentiment analysis with Doc2Vec and an integration of RFM and MBA
├── README.md
└── presentation.pdf                # slides presenting the results obatained and the marketing strategies developed
```
