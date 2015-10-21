package com.ai.project;

import twitter4j.*;

import java.io.IOException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

/**
 * Service to poll Twitter search data and store to MongoDB.
 */
public class TwitterSearchPoll {
    public static final String TV_SHOW_TAGS = "#thewalkingdead OR walking dead OR big bang theory" +
            "OR south park OR american horror story OR modern family OR heroes reborn OR family guy OR #arrow";

    private static final long ONE_DAY = 1000 * 60 * 60 * 24;
    private static final String twdQuery = "#thewalkingdead since:2015-10-18 until:2015-10-19";

    private TwitterStreamingFeed twitterStream;

    public TwitterSearchPoll() {
        twitterStream = new TwitterStreamingFeed();
    }

    public void pollTwitter() {
        try {
            String query = buildQuery(TV_SHOW_TAGS);
            searchTwitter(query);
        }
        catch (Exception ex) {
            System.err.println("Error querying for TWD tweets");
        }
    }

    private String buildQuery(String tags) {
        Date curDate = new Date();
        Date yesterday = new Date(curDate.getTime() - ONE_DAY);
        Date twoDaysAgo = new Date(curDate.getTime() - ONE_DAY * 2);
        DateFormat dateFormat = new SimpleDateFormat("YYYY-MM-dd");

        String twoDaysAgoStr = dateFormat.format(twoDaysAgo);
        String yesterdayDateString = dateFormat.format(yesterday);
        System.out.println("Query: " + tags + " since:" + twoDaysAgoStr + " until:" + yesterdayDateString);

        return tags + " since:" + twoDaysAgoStr + " until:" + yesterdayDateString;
    }

    public void load() throws InterruptedException, IOException {
        twitterStream.loadMenu("movieratings_search");
    }

    private void searchTwitter(String searchQuery) throws IOException {
        try {
            TwitterFactory tf = new TwitterFactory (twitterStream.getConfig());
            Twitter twitter = tf.getInstance ();

            Query query = new Query(searchQuery);
            QueryResult result = twitter.search(query);

            do {
                List<Status> tweets = result.getTweets();

                for (Status tweet : tweets) {
                    twitterStream.pushStatusToDB(tweet);
                }

                query = result.nextQuery();

                if (query != null) {
                    result = twitter.search(query);
                }
            } while(query != null);
        }
        catch (TwitterException ex) {
            System.err.println("Unable to access Twitter: " + ex.getMessage());
        }
    }

    public static void main(String[] args) throws InterruptedException, IOException {
        TwitterSearchPoll searchPoll = new TwitterSearchPoll();
        searchPoll.load();

        while (true) {
            searchPoll.pollTwitter();
            Thread.sleep(ONE_DAY);
        }
    }
}
