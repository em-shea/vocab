# Email Announcements

To include an announcement (new feature release, etc.) in a weekly email, upload a file to the S3 announcements bucket (referred to as VocabAnnouncementsBucket in SAM). 

The file(s) should be titled the date you want to publish the announcements in this format: 2020-07-10.json

The file contents should look like this:

{
  "message": "Check out this new feature!"
}

Note that dates are processed as UTC, for example at 5PM PST it will technically be the next day in UTC.