/**
 * Created by oktaygardener on 30/09/15.
 */
package com.ai.project;

import java.net.UnknownHostException;
import java.util.Scanner;
import com.mongodb.*;
import twitter4j.*;
import twitter4j.conf.ConfigurationBuilder;

public class TwitterStreamingFeed {

    //  Create necessary CB, DB, DBC
    private ConfigurationBuilder cb;
    private DB db;
    private DBCollection items;
    private MongoClient client;
    private MongoClientURI uri;
    // Keywords for the Twitter query
    public String[] keywords;
    public String consumerKey;
    public String consumerSecret;
    public String accessToken;
    public String tokenSecret;

    public String companyChoice;

    public static void main(String[] args) throws InterruptedException {

        TwitterStreamingFeed stream = new TwitterStreamingFeed();
        stream.loadMenu();

    }

    public void loadMenu() throws InterruptedException {
        Scanner input = new Scanner(System.in);
        input.close();
        companyChoice = "TV Shows";
        // OktayGardener keys
        consumerKey         = "NnzBdGJvRLBqJJwpSo3EuG0YK";
        consumerSecret      = "e4vv9S0ojWMpwyAa4eKNPlt7qg2GkgKOAXGJJTHnRZyVAwBw6I";
        accessToken         = "29536418-w8pU1DCRlhNVPvxF9cTe8iCizVadmDffY8xRCILBl";
        tokenSecret         = "y9Zraq20zz6rmHBYvFri1gM1kcSPxryC82BlEnywxYz6m";
        keywords = new String[]
                {"Big bang Theory",
                "Walking Dead",
                "South Park",
                "American Horror Story",
                "Modern Family",
                "Heroes Reborn",
                "Family Guy",
                "Arrow"};
        System.out.println("Now listening for tweets about.. " + companyChoice);

        // Connect to the database
        connectToDB();

        // Twitter AUTH Stuff
        cb = new ConfigurationBuilder();
        cb.setDebugEnabled(true);
        cb.setOAuthConsumerKey(consumerKey);
        cb.setOAuthConsumerSecret(consumerSecret);
        cb.setOAuthAccessToken(accessToken);
        cb.setOAuthAccessTokenSecret(tokenSecret);
        TwitterStream twitterStream = new TwitterStreamFactory(cb.build()).getInstance();

        // Class for listening on statuses
        StatusListener listener = new StatusListener() {

            public void onStatus(Status status) {
                // Print some tweet data to terminal window (output)
                // Make sure that the language is english
                if( status.getLang().equals("en")) {
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
                    for(String key : keywords) {
                        if(status.getText().toLowerCase().contains(key.toLowerCase())) {
                            basicObj.put("show_title", key);
                        }
                    }

                 //   basicObj.put("company", companyChoice);

                    // Insert the information into mongoDB
                    try {
                        items.insert(basicObj);
                    } catch (Exception e) {
                        System.out.println("MongoDB Connection Error : " + e.getMessage());

                    }
                } else{

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

    public void connectToDB() {
        try {
            // on constructor load initialize MongoDB and load collection
            initMongoDB();
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
    public void initMongoDB() throws MongoException {
        try {
            System.out.println("Connecting to Mongo DB..");
            //Mongo mongo;
            //mongo = new Mongo("localhost");
            uri = new MongoClientURI("mongodb://localhost/movieratings");
            client = new MongoClient(uri);
        } catch (UnknownHostException ex) {
            System.out.println("MongoDB Connection Error :" + ex.getMessage());
        }
    }
}
