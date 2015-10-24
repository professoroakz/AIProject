/**
 * Created by oktaygardener on 30/09/15.
 */
package com.ai.project;

import com.mongodb.*;
import twitter4j.*;
import twitter4j.conf.Configuration;
import twitter4j.conf.ConfigurationBuilder;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.net.UnknownHostException;
import java.util.HashMap;
import java.util.Scanner;

public class TwitterStreamingFeed {

    //  Create necessary CB, DB, DBC
    private ConfigurationBuilder cb;
    private DB db;
    private DBCollection items;
    private MongoClient client;
    private MongoClientURI uri;
    // Keywords for the Twitter query
    public String[] keywords;
    public HashMap<String, String[]> handles;
    public String consumerKey;
    public String consumerSecret;
    public String accessToken;
    public String tokenSecret;

    public String companyChoice;

    public static void main(String[] args) throws InterruptedException, IOException {

        TwitterStreamingFeed stream = new TwitterStreamingFeed();
        stream.loadMenu("movieratings_stream");
        stream.streamTweets();
    }

    public void loadMenu(String dbName) throws InterruptedException, IOException {
        Scanner input = null;
        InputStream fileStream = null;
        try {
            fileStream = getClass().
                    getResourceAsStream("/keys.cfg");
            input = new Scanner(fileStream);
            consumerKey = input.nextLine();
            consumerSecret = input.nextLine();
            accessToken = input.nextLine();
            tokenSecret = input.nextLine();
        }
        catch (Exception ex) {
            System.err.println("Unable to locate keys configuration file.");
            throw new FileNotFoundException();
        }
        finally {
            if (input != null) {
                input.close();
            }
            if (fileStream != null) {
                fileStream.close();
            }
        }
        companyChoice = "TV Shows";
        keywords = new String[]
                {"Big bang Theory",
                        "Walking Dead",
                        "South Park",
                        "American Horror Story",
                        "Modern Family",
                        "Heroes Reborn",
                        "Family Guy",
                        "Arrow"};
        handles = new HashMap<String, String[]>();
        handles.put(keywords[0], new String[]{"bigbang_cbs"});
        handles.put(keywords[1], new String[]{"twd", "walkingdead"});
        handles.put(keywords[2], new String[]{"southpark"});
        handles.put(keywords[3], new String[]{"ahsfx"});
        handles.put(keywords[4], new String[]{"heroes", "heroesreborn"});
        handles.put(keywords[5], new String[]{"modernfam"});
        handles.put(keywords[6], new String[]{"familyguy"});
        handles.put(keywords[7], new String[]{"cw_arrow"});
        System.out.println("Now listening for tweets about.. " + companyChoice);

        // Connect to the database
        connectToDB(dbName);

        // Twitter AUTH Stuff
        cb = new ConfigurationBuilder();
        cb.setDebugEnabled(true);
        cb.setOAuthConsumerKey(consumerKey);
        cb.setOAuthConsumerSecret(consumerSecret);
        cb.setOAuthAccessToken(accessToken);
        cb.setOAuthAccessTokenSecret(tokenSecret);
    }

    public Configuration getConfig() {
        return cb.build();
    }

    public void pushStatusToDB(Status status) {
        String text, showTitle;
        // Print some tweet data to terminal window (output)
        // Make sure that the language is english
        if (status.getLang().equals("en")) {
            System.out.println("@" + status.getUser().getScreenName() + ": " + status.getText() +
                    "\nuser_location: " + status.getUser().getLocation() +
                    "\ncreated_at: " + status.getCreatedAt() + "\n" +
                    "language:: " + status.getLang());
            // JSON object
            BasicDBObject basicObj = new BasicDBObject();
            // Information from the status (tweet)
            basicObj.put("user_name", status.getUser().getScreenName());
            basicObj.put("tweet_followers_count", status.getUser().getFollowersCount());
            basicObj.put("user_location", status.getUser().getLocation());
            basicObj.put("created_at", status.getCreatedAt());

            // External information around the status (tweet)
            UserMentionEntity[] mentioned = status.getUserMentionEntities();
            basicObj.put("tweet_mentioned_count", mentioned.length);
            basicObj.put("tweet_ID", status.getId());
            basicObj.put("tweet_text", status.getText());
            basicObj.put("show_title", getShowTitle(status, status.getText()));

            // Insert the information into mongoDB
            try {
                items.insert(basicObj);
            } catch (Exception e) {
                System.out.println("MongoDB Connection Error : " + e.getMessage());

            }
        } else {

        }
    }

    public void streamTweets() throws InterruptedException {
        TwitterStream twitterStream = new TwitterStreamFactory(cb.build()).getInstance();

        // Class for listening on statuses
        StatusListener listener = new StatusListener() {

            public void onStatus(Status status) {
                String text, showTitle;
                // Print some tweet data to terminal window (output)
                // Make sure that the language is english
                if (status.getLang().equals("en")) {
                    System.out.println("@" + status.getUser().getScreenName() + ": " + status.getText() +
                            "\nuser_location: " + status.getUser().getLocation() +
                            "\ncreated_at: " + status.getCreatedAt() + "\n" +
                            "language:: " + status.getLang());
                    // JSON object
                    BasicDBObject basicObj = new BasicDBObject();
                    // Information from the status (tweet)
                    basicObj.put("user_name", status.getUser().getScreenName());
                    basicObj.put("tweet_followers_count", status.getUser().getFollowersCount());
                    basicObj.put("user_location", status.getUser().getLocation());
                    basicObj.put("created_at", status.getCreatedAt());

                    // External information around the status (tweet)
                    UserMentionEntity[] mentioned = status.getUserMentionEntities();
                    basicObj.put("tweet_mentioned_count", mentioned.length);
                    basicObj.put("tweet_ID", status.getId());
                    basicObj.put("tweet_text", status.getText());
                    basicObj.put("show_title", getShowTitle(status, status.getText()));

                    // Insert the information into mongoDB
                    try {
                        items.insert(basicObj);
                    } catch (Exception e) {
                        System.out.println("MongoDB Connection Error : " + e.getMessage());

                    }
                } else {

                }
            }

            // Needed methods for StatusListener (Ignore)
            public void onDeletionNotice(StatusDeletionNotice statusDeletionNotice) {
                System.out.println("Got a status deletion notice id:" + statusDeletionNotice.getStatusId());
            }

            public void onTrackLimitationNotice(int numberOfLimitedStatuses) {
                System.out.println("Got track limitation notice:" + numberOfLimitedStatuses);
            }

            public void onScrubGeo(long userId, long upToStatusId) {
                System.out.println("Got scrub_geo event userId:" + userId + " upToStatusId:" + upToStatusId);
            }

            public void onStallWarning(StallWarning stallWarning) {
                //To change body of implemented methods use File | Settings | File Templates.
            }

            public void onException(Exception ex) {
                ex.printStackTrace();
            }
        };

        // Create new query to twitter
        FilterQuery fq = new FilterQuery();

        fq.track(keywords);
        twitterStream.addListener(listener);
        twitterStream.filter(fq);

    }

    public void connectToDB(String dbName) {
        try {
            // on constructor load initialize MongoDB and load collection
            initMongoDB(dbName);
            db = client.getDB(uri.getDatabase());
            items = db.getCollection("tweets");

        } catch (MongoException ex) {
            System.out.println("MongoException :" + ex.getMessage());
        }
    }

    /**
     * initMongoDB been called in constructor so every object creation this
     * initialize MongoDB, if database doesn't exist
     */
    public void initMongoDB(String dbName) throws MongoException {
        try {
            System.out.println("Connecting to Mongo DB..");
            //Mongo mongo;
            //mongo = new Mongo("localhost");
            uri = new MongoClientURI("mongodb://localhost/" + dbName);
            client = new MongoClient(uri);
        } catch (UnknownHostException ex) {
            System.out.println("MongoDB Connection Error :" + ex.getMessage());
        }
    }

    private String getShowTitle(Status status, String text) {
        String title = null;
        String lowerCaseText = text.toLowerCase();

        for (String key : keywords) {
            if (lowerCaseText.contains(key.toLowerCase())) {
                title = key;
            }
        }
        if (title == null) {
            title = titleFromHandles(lowerCaseText);
        }
        if (title == null) {
            System.out.println("Title undetermined");
            title = "undetermined";
        }

        return title;
    }

    private String titleFromHandles(String lowercaseText) {
        for (String showTitle : handles.keySet()) {
            for (String handle : handles.get(showTitle)) {
                if (lowercaseText.contains(handle)) {
                    return showTitle;
                }
            }
        }

        return null;
    }
}
