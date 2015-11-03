package com.ai.project;

import twitter4j.*;

import java.io.IOException;
import java.lang.Exception;
import java.lang.InterruptedException;
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
    public static final String[] TV_SHOWS = {"Big bang Theory",
        "Walking Dead",
        "South Park",
        "American Horror Story",
        "Modern Family",
        "Heroes Reborn",
        "Family Guy",
        "Arrow"};

    private static final long ONE_DAY = 1000 * 60 * 60 * 24;
    private static final String twdQuery = "#thewalkingdead since:2015-10-18 until:2015-10-19";

    private TwitterStreamingFeed twitterStream;

    public TwitterSearchPoll() {
        twitterStream = new TwitterStreamingFeed();
    }

    /**
     * @return True if successful, false if Twitter error.
     */
    public boolean pollTwitter(String showTitle) {
        // TODO: modify to query for one show every 15 minutes until all shows have been queried for.
        boolean successful = true;
        String query = buildQuery(showTitle);

        try {
            searchTwitter(query, showTitle);
        }
        catch (TwitterException ex) {
            // If not caused by exceeding rate, unsuccessful
            if (ex.exceededRateLimitation()) {
                System.err.println(
                    "Streaming rate exceeded:\n" + "Retry in " + ex.getRetryAfter() + " seconds.");
            }
            else {
                successful = false;
            }
        }
        catch (Exception ex) {
            successful = false;
        }

        return successful;
    }

    /**
     * Polls Twitter every minute until the poll was successful.
     * @return Time offset in milliseconds taken to successfully poll Twitter.
     */
    public long pollUntilSuccess(String showTitle) {
        boolean success = false;
        int timeTaken = 0;
        long ONE_MINUTE = 1000 * 60;

        while (!success) {
            success = pollTwitter(showTitle);

            if (!success) {
                try {
                    Thread.sleep(ONE_MINUTE);
                    timeTaken += ONE_MINUTE;
                }
                catch (InterruptedException ex) {
                    System.err.println("Thread.sleep interrupted: " + ex.getMessage());
                }
            }
        }

        return timeTaken;
    }

    private String buildQuery(String showTitle) {
        Date curDate = new Date();
        Date yesterday = new Date(curDate.getTime() - ONE_DAY);
        Date twoDaysAgo = new Date(curDate.getTime() - ONE_DAY * 2);
        DateFormat dateFormat = new SimpleDateFormat("YYYY-MM-dd");

        String twoDaysAgoStr = dateFormat.format(twoDaysAgo);
        String yesterdayDateString = dateFormat.format(yesterday);
        System.out.println("Query: " + showTitle + " since:" + twoDaysAgoStr + " until:" + yesterdayDateString);

        return showTitle + " since:" + twoDaysAgoStr + " until:" + yesterdayDateString;
    }

    public void load() throws InterruptedException, IOException {
        twitterStream.loadMenu("movieratings_search");
    }

    private void searchTwitter(String searchQuery, String showTitle) throws IOException, TwitterException {
        try {
            TwitterFactory tf = new TwitterFactory(twitterStream.getConfig());
            Twitter twitter = tf.getInstance();

            Query query = new Query(searchQuery);
            QueryResult result = twitter.search(query);

            do {
                List<Status> tweets = result.getTweets();

                for (Status tweet : tweets) {
                    twitterStream.pushStatusToDB(tweet, showTitle);
                }

                query = result.nextQuery();

                if (query != null) {
                    result = twitter.search(query);
                }
            } while (query != null);
        }
        catch (TwitterException ex) {
            System.err.println("Unable to access Twitter: " + ex.getMessage());

            if (ex.exceededRateLimitation()) {
                throw ex;
            }
        }
    }

//    private void searchTwitter(String searchQuery) throws IOException, TwitterException {
//        try {
//            TwitterFactory tf = new TwitterFactory(twitterStream.getConfig());
//            Twitter twitter = tf.getInstance();
//
//            Query query = new Query(searchQuery);
//            QueryResult result = twitter.search(query);
//
//            do {
//                List<Status> tweets = result.getTweets();
//
//                for (Status tweet : tweets) {
//                    twitterStream.pushStatusToDB(tweet);
//                }
//
//                query = result.nextQuery();
//
//                if (query != null) {
//                    result = twitter.search(query);
//                }
//            } while (query != null);
//        }
//        catch (TwitterException ex) {
//            System.err.println("Unable to access Twitter: " + ex.getMessage());
//
//            if (ex.exceededRateLimitation()) {
//                throw ex;
//            }
//        }
//    }

    public static void main(String[] args) throws InterruptedException, IOException {
        long timeOffset = 0;
        long twentyMinutes = 1000 * 60 * 20;
        boolean successfulPoll = true;
        TwitterSearchPoll searchPoll = new TwitterSearchPoll();
        searchPoll.load();
        while (true) {
            for (String show : TV_SHOWS) {
                timeOffset += searchPoll.pollUntilSuccess(show);
                timeOffset += twentyMinutes;
                Thread.sleep(twentyMinutes);
            }
            Thread.sleep(ONE_DAY - timeOffset);
            timeOffset = 0;
        }
    }
}
